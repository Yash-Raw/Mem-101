"""The durability gate: what survives the session.

Beginner's `session-vs-longterm` lab built these rules and used them only to
*analyse* the store. Here they move onto the write path, where they belong --
the decision "is this worth keeping forever" happens once, at write time,
before knowing what will be asked.

Rules, not a model call. Explicit markers and claim shape are cheap, auditable,
and catch most of it; keeping this deterministic is also what lets the fixture
tables stay hand-authorable (one LLM call per turn, on extraction alone).
"""
from __future__ import annotations

from ..types import Memory, MemoryType, Tier

EXPLICIT = (
    "keep that in mind", "memorise", "memorize", "from now on",
    "filing that away", "always in that order",
)
ACTIVITY = ("debugging", "completed her first week", "planning a trip")
IMPERATIVE = ("asked to forget", "asked to delete")


def tier_for(memory: Memory, turn_text: str = "") -> Tier:
    if any(marker in turn_text.lower() for marker in EXPLICIT):
        return Tier.LONG_TERM
    if any(marker in memory.content for marker in IMPERATIVE):
        # A request is not a fact. It is kept -- honouring it is a governance
        # problem that lands in Advanced -- but it does not earn long-term tier.
        return Tier.SCRATCH
    if memory.type is MemoryType.PROCEDURAL:
        return Tier.LONG_TERM
    if any(marker in memory.content for marker in ACTIVITY):
        return Tier.SCRATCH if memory.type is MemoryType.EPISODIC else Tier.WORKING
    return Tier.LONG_TERM


def passes(memory: Memory, turn_text: str = "") -> bool:
    """Does this candidate earn a slot in the durable store?

    Scratch-tier memories are dropped at write time. Everything else is kept --
    including things that will later be forgotten, because deciding *that*
    needs usage signals this stage does not have.
    """
    return tier_for(memory, turn_text) is not Tier.SCRATCH
