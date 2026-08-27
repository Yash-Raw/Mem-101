"""Reference solution."""
from __future__ import annotations

from memlab.types import Memory, MemoryType, Tier

EXPLICIT = ("keep that in mind", "memorise", "from now on", "filing that away", "always in that order")
ACTIVITY = ("debugging", "completed her first week", "planning a trip", "is leaving")
IMPERATIVE = ("asked to forget", "asked to delete")


def promotion_tier(memory: Memory, turn_text: str = "") -> Tier:
    """Rules first: cheap, auditable, and it catches most of it."""
    if any(marker in turn_text.lower() for marker in EXPLICIT):
        return Tier.LONG_TERM
    if any(marker in memory.content for marker in IMPERATIVE):
        return Tier.SCRATCH  # a request is not a fact
    if memory.type is MemoryType.PROCEDURAL:
        return Tier.LONG_TERM
    if any(marker in memory.content for marker in ACTIVITY):
        return Tier.SCRATCH if memory.type is MemoryType.EPISODIC else Tier.WORKING
    if memory.type is MemoryType.EPISODIC and "was diagnosed" not in memory.content:
        return Tier.WORKING if "moved" in memory.content or "promotion" in memory.content \
            else Tier.LONG_TERM
    return Tier.LONG_TERM


def would_promote(memories: list[Memory], turns: dict[str, str]) -> dict[Tier, list[Memory]]:
    out: dict[Tier, list[Memory]] = {t: [] for t in Tier}
    for m in memories:
        out[promotion_tier(m, turns.get(m.provenance.source_id, ""))].append(m)
    return out
