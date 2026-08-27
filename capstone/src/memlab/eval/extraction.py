"""Scoring the write path.

Recall on a memory layer is not "did retrieval find it" -- it is "was it ever
written down in a form a question could reach". Those are different failures
with the same symptom, and only the first is fixable at read time.

So this scores extraction against `gold.yml` on two axes:

  state_recall     of the facts the exam needs, how many exist as a live
                   SEMANTIC claim -- an episode does not count, because a
                   question about the present cannot reach one
  reachability     of those, how many actually surface in the top-k for the
                   question they exist to answer
  over_extraction  the share of records a durability gate would drop, i.e.
                   what fraction of the store is competing for token budget
                   forever without earning it

The gap between the first two is the interesting number, and it is invisible to
any store-shaped check. Beginner writes an employer state -- "Priya is at Calico
now" -- and scores full recall. It ranks 35th of 36, because it contains no word
a question about employment would use. Written is not the same as reachable, and
extraction owns both.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..extract.gate import passes
from ..retrieve.embedding import EmbeddingRetriever
from ..types import Memory, MemoryType, Scope

# The states the session-14 question needs, from gold.yml's final_question.
REQUIRED_STATES = {
    "employer": ("works at Calico", "is at Calico"),
    "no meat": ("does not eat meat",),
    "gluten": ("gluten intolerance",),
    "fish permitted": ("eats fish", "pescatarian"),
}

# The question each required state exists to answer.
NATURAL_QUERY = {
    "employer": "where do I work?",
    "no meat": "what should I not eat?",
    "gluten": "what should I not eat?",
    "fish permitted": "can I eat fish?",
}


@dataclass
class ExtractionScore:
    total: int
    state_recall: float
    reachability: float
    found: dict[str, bool]
    reached: dict[str, int | None]
    over_extracted: list[str]

    @property
    def over_extraction_rate(self) -> float:
        return len(self.over_extracted) / self.total if self.total else 0.0


def score(
    memories: list[Memory],
    turns: dict[str, str] | None = None,
    scope: Scope | None = None,
    k: int = 10,
) -> ExtractionScore:
    turns = turns or {}
    scope = scope or Scope(user="priya")
    semantic = [m for m in memories if m.type is MemoryType.SEMANTIC and m.is_live]
    retriever = EmbeddingRetriever()

    found: dict[str, bool] = {}
    reached: dict[str, int | None] = {}

    for name, keys in REQUIRED_STATES.items():
        found[name] = any(any(key in m.content for key in keys) for m in semantic)
        hits = retriever.search(NATURAL_QUERY[name], memories, scope, k=k, live_only=True)
        reached[name] = next(
            (i for i, h in enumerate(hits, 1) if any(key in h.memory.content for key in keys)),
            None,
        )

    over = [
        m.content for m in memories
        if not passes(m, turns.get(m.provenance.source_id, ""))
    ]
    return ExtractionScore(
        total=len(memories),
        state_recall=sum(found.values()) / len(found),
        reachability=sum(r is not None for r in reached.values()) / len(reached),
        found=found,
        reached=reached,
        over_extracted=over,
    )
