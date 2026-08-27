"""Reference solution."""
from __future__ import annotations

from memlab.extract.router import RULES
from memlab.types import Memory


def can_contradict(memory: Memory) -> bool:
    """Only a live claim about *now* can be made false by another claim."""
    return RULES[memory.type].can_contradict and memory.is_live


def partition_by_conflict_risk(
    memories: list[Memory],
) -> tuple[list[Memory], list[Memory]]:
    """(at risk, structurally safe) -- by type alone, before any comparison."""
    at_risk = [m for m in memories if can_contradict(m)]
    safe = [m for m in memories if not can_contradict(m)]
    return at_risk, safe


def comparisons_avoided(memories: list[Memory]) -> tuple[int, int]:
    """Pairs a naive detector would check, vs pairs that could matter."""
    n = len(memories)
    at_risk, _ = partition_by_conflict_risk(memories)
    r = len(at_risk)
    return n * (n - 1) // 2, r * (r - 1) // 2
