"""Per-type rules: what the type actually decides.

Beginner treated MemoryType as a label. Here it becomes the thing that governs
a memory's whole life -- whether it can go stale, what happens when two of them
disagree, and what a correct update looks like.

The column that matters is `can_contradict`. Only a claim about *now* can be
contradicted by another claim about now, so almost every mechanism in this level
applies to exactly one of the four types. An episode that disagrees with another
episode is just two things that happened.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..types import Memory, MemoryType


@dataclass(frozen=True)
class TypeRule:
    can_contradict: bool     # can another memory of this type make it false?
    expires: bool            # does it stop being true on its own?
    on_conflict: str         # what a correct update does
    retrieved_by: str        # the query shape that should surface it


RULES: dict[MemoryType, TypeRule] = {
    MemoryType.EPISODIC: TypeRule(
        can_contradict=False, expires=False,
        on_conflict="keep both -- two things happened",
        retrieved_by="time, participants",
    ),
    MemoryType.SEMANTIC: TypeRule(
        can_contradict=True, expires=True,
        on_conflict="one must retire",
        retrieved_by="topic",
    ),
    MemoryType.PROCEDURAL: TypeRule(
        can_contradict=True, expires=True,
        on_conflict="replace wholesale -- steps are not independently updatable",
        retrieved_by="task, not topic",
    ),
    MemoryType.WORKING: TypeRule(
        can_contradict=False, expires=True,
        on_conflict="irrelevant -- dies with the session",
        retrieved_by="position",
    ),
}

# Verbs that describe a transition rather than a condition. A turn built around
# one of these is an event, and the state it produces has to be derived.
CHANGE_VERBS = (
    "leaving", "left", "starting", "started", "joined", "moved", "changed",
    "got a promotion", "was diagnosed", "quit", "switched",
)


def rule_for(memory: Memory) -> TypeRule:
    return RULES[memory.type]


def can_contradict(memory: Memory) -> bool:
    return rule_for(memory).can_contradict and memory.is_live


def describes_a_change(text: str) -> bool:
    """Does this turn report a transition? If so, a state is owed."""
    lowered = text.lower()
    return any(v in lowered for v in CHANGE_VERBS)
