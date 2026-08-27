"""How much a memory matters -- as distinct from how well it matches a query.

Every memory in the store sits at salience 0.5 with `access_count` 0. The
fields were designed in Beginner and nothing has ever populated them, so the
system cannot tell a fact Priya insisted on from an afternoon's debugging.

Salience is **importance**, not relevance. Relevance is a property of a query
and is computed at read time; salience is a property of the memory and is
computed once and updated as evidence arrives. Conflating them is how systems
end up ranking by "what looks like the question" and calling it memory.

Four signals, all read off fields that already exist:

    explicit       the user said to remember it
    corroboration  independent sources, via `derived_from`
    use            `access_count` -- it keeps being recalled and used
    authority      a relayed claim matters less than a first-party one

Rules, not a model. A salience score that varies between runs cannot be
debugged, and a user asking "why did you forget that?" deserves an answer.
"""
from __future__ import annotations

from dataclasses import replace

from ..extract.gate import ACTIVITY, EXPLICIT
from ..types import Memory, MemoryType

BASE = 0.5

EXPLICIT_BONUS = 0.30      # "keep that in mind", "always in that order"
CORROBORATION_BONUS = 0.10  # per independent supporting source
USE_BONUS = 0.05           # per recall that was actually assembled
ACTIVITY_PENALTY = 0.25    # a finished activity is not a standing fact
HEARSAY_PENALTY = 0.20     # relayed, unconfirmed

# Procedures are taught once, deliberately, and rarely restated -- so the
# reinforcement signals under-serve them badly. This is a correction for a
# known blind spot, not a general preference for the type.
PROCEDURE_BONUS = 0.15


def score(memory: Memory, turn_text: str = "") -> float:
    """Importance in [0, 1]. Deterministic, and explicable line by line."""
    value = BASE

    if any(marker in turn_text.lower() for marker in EXPLICIT):
        value += EXPLICIT_BONUS
    if memory.type is MemoryType.PROCEDURAL:
        value += PROCEDURE_BONUS

    value += CORROBORATION_BONUS * len(memory.derived_from)
    value += USE_BONUS * memory.access_count

    if any(marker in memory.content for marker in ACTIVITY):
        value -= ACTIVITY_PENALTY
    if memory.provenance.authority < 0.5:
        value -= HEARSAY_PENALTY

    return round(min(1.0, max(0.0, value)), 3)


def apply(memories: list[Memory], turns: dict[str, str] | None = None) -> list[Memory]:
    turns = turns or {}
    return [
        replace(m, salience=score(m, turns.get(m.provenance.source_id, "")))
        for m in memories
    ]


def record_use(memories: list[Memory], used_ids: set[str]) -> list[Memory]:
    """Retrieval feedback: a memory that was recalled AND assembled has earned it.

    The strongest available signal and the only one that needs the system to
    have been running -- which is why it cannot be the only one.
    """
    return [
        replace(m, access_count=m.access_count + 1) if m.id in used_ids else m
        for m in memories
    ]
