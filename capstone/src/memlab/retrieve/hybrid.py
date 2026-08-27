"""Ranking with the signals a memory store actually has.

Plain cosine answers "what looks like the question" and the store has four
other signals it has never consulted. Three of them exist because earlier
modules put them there:

    similarity   what the question is about                (Beginner)
    coverage     how much of the question's vocabulary the
                 memory actually contains                  (this module)
    recency      when the fact was true                    (event time, Beginner)
    salience     how much the memory matters               (I5)
    type match   does this SHAPE of memory answer this
                 SHAPE of question                         (this module)
    subject      is this memory even ABOUT the person
                 being asked about                         (entities, I2)
    slot         does it fill the ATTRIBUTE the question
                 asks about                                (SLOTS, I4)

The last one is the interesting one, and it is why `salience-scoring` found
that adding importance to a relevance score made things worse. A taught
procedure is permanently important and almost never the answer to a factual
question. Weighting it up is right; surfacing it for "what should I not eat" is
not. Type match is what separates those.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..llm.fake import cosine, embed_text
from ..retrieve.embedding import Hit
from ..types import Memory, MemoryType, Scope

WORD = re.compile(r"[a-z0-9']+")

# Deliberately modest weights on everything except similarity: this is a
# re-ranking of a relevance signal, not a replacement for one.
W_SIMILARITY = 1.00
W_COVERAGE = 0.50
W_RECENCY = 0.20
W_SALIENCE = 0.15
W_TYPE = 0.50
W_SUBJECT = 0.40
W_SLOT = 0.60

RECENCY_SPAN = timedelta(days=730)


class Intent(str):
    """What shape of answer the question wants."""

    STATE = "state"        # "where do I work" -> a current fact
    HISTORY = "history"    # "when did I" -> an episode
    PROCEDURE = "procedure"  # "how do I" -> a workflow


# Which memory type answers which question shape. Not a ban -- a preference.
AFFINITY: dict[str, dict[MemoryType, float]] = {
    Intent.STATE: {
        MemoryType.SEMANTIC: 1.0,
        MemoryType.EPISODIC: 0.0,
        MemoryType.PROCEDURAL: 0.0,
        MemoryType.WORKING: 0.0,
    },
    Intent.HISTORY: {
        MemoryType.EPISODIC: 1.0,
        MemoryType.SEMANTIC: 0.5,
        MemoryType.PROCEDURAL: 0.0,
        MemoryType.WORKING: 0.0,
    },
    Intent.PROCEDURE: {
        MemoryType.PROCEDURAL: 1.0,
        MemoryType.SEMANTIC: 0.2,
        MemoryType.EPISODIC: 0.0,
        MemoryType.WORKING: 0.0,
    },
}

HOW_TO = ("how do i", "how should i", "what is my process", "walk me through", "run my")
WHEN = ("when did", "when was", "what happened", "how long ago", "last time")


def intent_of(query: str) -> str:
    """Rules, on the read path. One model call per turn belongs to extraction."""
    lowered = query.lower()
    if any(marker in lowered for marker in HOW_TO):
        return Intent.PROCEDURE
    if any(marker in lowered for marker in WHEN):
        return Intent.HISTORY
    return Intent.STATE


# Light stemming. `work` and `works` must match, or a query about employment
# scores zero against the memory that answers it.
STOPWORDS = frozenset(
    ["where", "do", "does", "did", "i", "my", "me", "the", "a", "an", "is", "are", "was", "at", "to", "and", "or", "of", "what", "should", "not", "how", "when", "why", "who"]
)


def terms(text: str) -> set[str]:
    words = {w.rstrip("s") if len(w) > 3 and w.endswith("s") and not w.endswith("ss")
             else w for w in WORD.findall(text.lower())}
    return words - STOPWORDS


def coverage(query: str, content: str) -> float:
    """How much of the QUESTION's vocabulary this memory contains.

    Deliberately not Jaccard. Jaccard divides by the union, so a long, correct
    memory scores below a short, wrong one -- "Priya works at Calico Systems"
    lost to "Sam still works nights" purely on length. Coverage asks what the
    question wanted and ignores what else the memory happens to say.
    """
    wanted = terms(query)
    return len(wanted & terms(content)) / len(wanted) if wanted else 0.0


def subject_match(memory: Memory, scope: Scope) -> float:
    """Is this memory about the person being asked about?

    A first-person question is about the account holder. `Sam still works
    nights` is a perfectly good memory and answers nothing Priya asked about
    herself -- it survives every other signal because it shares the word.
    """
    subject = frozenset(memory.entities) or frozenset({scope.user})
    return 1.0 if subject == frozenset({scope.user}) else 0.0


def recency(memory: Memory, now: datetime) -> float:
    """1.0 for today, falling to 0 across the span. Event time, not ingestion."""
    age = now - (memory.happened_at or memory.recorded_at)
    return max(0.0, 1.0 - (age / RECENCY_SPAN))


@dataclass
class Scored:
    memory: Memory
    total: float
    parts: dict[str, float]


def slot_match(memory: Memory, wanted: set[str]) -> float:
    """Does this memory fill the attribute the question asks about?

    The strongest signal available, and the one that finds facts sharing no
    vocabulary with the question -- "Priya has a gluten intolerance" against
    "what should I not eat". Without it every fact about the user scores about
    the same, because they all match on the user's name and nothing else.

    Reuses the SLOTS table from `contradiction-detection`. One vocabulary, used
    by the write path to group conflicting beliefs and by the read path to find
    relevant ones.
    """
    from ..evolve.conflict import slot_of

    return 1.0 if wanted and slot_of(memory) in wanted else 0.0


def score_one(
    query: str,
    memory: Memory,
    now: datetime,
    intent: str,
    scope: Scope,
    wanted_slots: set[str] | None = None,
    query_vector: list[float] | None = None,
    index=None,
) -> Scored:
    q = query_vector if query_vector is not None else embed_text(query)
    content_vector = index.vector_for(memory) if index is not None else embed_text(memory.content)
    parts = {
        "similarity": W_SIMILARITY * cosine(q, content_vector),
        "coverage": W_COVERAGE * coverage(query, memory.content),
        "recency": W_RECENCY * recency(memory, now),
        "salience": W_SALIENCE * memory.salience,
        "type": W_TYPE * AFFINITY[intent][memory.type],
        "subject": W_SUBJECT * subject_match(memory, scope),
        "slot": W_SLOT * slot_match(memory, wanted_slots or set()),
    }
    return Scored(memory=memory, total=round(sum(parts.values()), 4), parts=parts)


def rank(
    query: str, memories: list[Memory], scope: Scope, k: int = 5, index=None
) -> list[Hit]:
    """Signature matches EmbeddingRetriever.search, so it drops into Pipeline.

    With an index, the query is embedded once and every memory vector is served
    from cache -- 2N embed calls per query become one.
    """
    if not memories:
        return []
    from .query import slots_for

    now = max((m.happened_at or m.recorded_at) for m in memories)
    intent = intent_of(query)
    wanted = slots_for(query)
    q = embed_text(query)
    scored = [
        score_one(query, m, now, intent, scope, wanted, query_vector=q, index=index)
        for m in memories
    ]
    scored.sort(key=lambda s: -s.total)
    return [Hit(memory=s.memory, score=s.total) for s in scored[:k]]
