"""Lab: six signals, and the one that reaches what words cannot.

    uv run python curriculum/intermediate/hybrid-ranking/lab/lab.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from memlab.llm.fake import cosine, embed_text
from memlab.retrieve.embedding import Hit
from memlab.types import Memory, MemoryType, Scope

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
    """TODO: what fraction of the QUESTION's terms appear in this memory?

    Not Jaccard -- dividing by the union makes a long correct memory lose to a
    short wrong one. Divide by the query's terms only.
    """
    raise NotImplementedError("implement coverage")


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
    """TODO: 1.0 if this memory fills one of the attributes asked about.

    Use evolve.conflict.slot_of -- the same table the write path uses to group
    conflicting beliefs. This is the term that finds "has a gluten intolerance"
    for "what should I not eat", which share no words at all.
    """
    raise NotImplementedError("implement slot_match")


def score_one(
    query: str,
    memory: Memory,
    now: datetime,
    intent: str,
    scope: Scope,
    wanted_slots: set[str] | None = None,
) -> Scored:
    parts = {
        "similarity": W_SIMILARITY * cosine(embed_text(query), embed_text(memory.content)),
        "coverage": W_COVERAGE * coverage(query, memory.content),
        "recency": W_RECENCY * recency(memory, now),
        "salience": W_SALIENCE * memory.salience,
        "type": W_TYPE * AFFINITY[intent][memory.type],
        "subject": W_SUBJECT * subject_match(memory, scope),
        "slot": W_SLOT * slot_match(memory, wanted_slots or set()),
    }
    return Scored(memory=memory, total=round(sum(parts.values()), 4), parts=parts)


def rank(query: str, memories: list[Memory], scope: Scope, k: int = 5) -> list[Hit]:
    """Signature matches EmbeddingRetriever.search, so it drops into Pipeline."""
    if not memories:
        return []
    from memlab.retrieve.query import slots_for

    now = max((m.happened_at or m.recorded_at) for m in memories)
    intent = intent_of(query)
    wanted = slots_for(query)
    scored = [score_one(query, m, now, intent, scope, wanted) for m in memories]
    scored.sort(key=lambda s: -s.total)
    return [Hit(memory=s.memory, score=s.total) for s in scored[:k]]


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.eval.exam import QUESTION
    from memlab.pipeline import at
    from memlab.retrieve.scoped import eligible
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-hybrid.jsonl")
    store.clear()
    ingest(store, scope, at("I5"))
    pool = eligible(store.all(), scope)

    hits = rank(QUESTION, pool, scope, k=len(pool))
    place = next(i for i, h in enumerate(hits, 1) if "works at Calico" in h.memory.content)
    print(f"employer rank: {place} of {len(pool)}\n")
    for i, h in enumerate(hits[:5], 1):
        print(f"  {i}. {h.score:.3f}  {h.memory.content[:52]}")

    now = max((m.happened_at or m.recorded_at) for m in pool)
    from memlab.retrieve.query import slots_for
    employer = next(m for m in pool if "works at Calico" in m.content)
    parts = score_one(QUESTION, employer, now, intent_of(QUESTION), scope,
                      slots_for(QUESTION)).parts
    print("\nwhy it ranked there:")
    for name, value in sorted(parts.items(), key=lambda kv: -kv[1]):
        print(f"   {name:<12} {value:.3f}")


if __name__ == "__main__":
    main()
