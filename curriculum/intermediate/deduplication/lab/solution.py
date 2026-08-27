"""Reference solution."""
from __future__ import annotations

from dataclasses import replace
from itertools import combinations

from memlab.evolve.dedupe import DUPLICATE_THRESHOLD, Merge
from memlab.llm.fake import cosine, embed_text
from memlab.types import Memory

NEAR_MISSES = [
    ("was diagnosed with a gluten", "has a gluten intolerance"),
    ("is leaving Northwind Labs", "left Northwind Labs last month"),
    ("Priya is vegetarian", "Priya is pescatarian"),
]


def _eligible(a: Memory, b: Memory) -> bool:
    return (
        a.type is b.type
        and a.is_live
        and b.is_live
        and a.scope.user == b.scope.user
        and set(a.entities) == set(b.entities)
    )


def duplicate_pairs(
    memories: list[Memory], threshold: float = DUPLICATE_THRESHOLD
) -> list[Merge]:
    vectors = {m.id: embed_text(m.content) for m in memories}
    found = []
    for a, b in combinations(memories, 2):
        if not _eligible(a, b):
            continue
        score = cosine(vectors[a.id], vectors[b.id])
        if score >= threshold:
            first, second = sorted((a, b), key=lambda m: (m.happened_at or m.recorded_at))
            found.append(Merge(kept=first, dropped=second, similarity=score))
    return found


def dedupe(memories: list[Memory]) -> list[Memory]:
    merges = duplicate_pairs(memories)
    dropped = {m.dropped.id for m in merges}
    corroborated = {m.kept.id for m in merges}

    out = []
    for memory in memories:
        if memory.id in dropped:
            continue
        if memory.id in corroborated:
            memory = replace(memory, confidence=min(1.0, memory.confidence + 0.1))
        out.append(memory)
    return out


def near_miss_scores(memories: list[Memory]) -> list[tuple[float, str, str]]:
    """The pairs a lower threshold would wrongly collapse."""
    out = []
    for left, right in NEAR_MISSES:
        a = next((m for m in memories if left in m.content), None)
        b = next((m for m in memories if right in m.content), None)
        if a and b:
            out.append((cosine(embed_text(a.content), embed_text(b.content)),
                        a.content, b.content))
    return sorted(out, reverse=True)
