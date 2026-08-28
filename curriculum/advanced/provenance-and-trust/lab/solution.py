"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from memlab.evolve.conflict import SLOTS, slot_of
from memlab.types import Memory

# What each writer is competent about. Deliberately explicit and deliberately
# short: a table you can read is a table someone will keep current, and the
# failure of a wrong entry here is visible in arbitration rather than silent.
COMPETENCE: dict[str, frozenset[str]] = {
    "user": frozenset(SLOTS),                      # first party, everything
    "calendar-agent": frozenset({"commute"}),      # schedules and movement
    "travel-agent": frozenset(),                   # relays; authoritative about nothing
}

# What a writer's authority is worth outside its competence. Not zero: an
# out-of-domain observation can still be evidence, and refusing to store it
# makes a later confirmation look like the first anyone had heard -- the
# argument I1 made for keeping hearsay at all.
OUT_OF_DOMAIN = 0.3


class Verdict(str, Enum):
    """Three outcomes, not two -- and the third is the one that matters.

    A claim naming no modelled slot is not out of the writer's domain; it is
    outside the *vocabulary*. Discounting it would punish a reliable agent for
    a gap in the SLOTS table, and the calendar agent's entire output falls
    here: this course models seven attributes and none of them is scheduling.
    """

    COMPETENT = "competent"        # within the writer's domain
    OUT_OF_DOMAIN = "out of domain"  # names a slot this writer does not own
    UNNAMEABLE = "unnameable"      # names no slot at all -- cannot be assessed


@dataclass(frozen=True)
class Assessment:
    memory: Memory
    slot: str | None
    verdict: Verdict
    trust: float

    @property
    def competent(self) -> bool:
        return self.verdict is Verdict.COMPETENT

    @property
    def checkable(self) -> bool:
        """Can arbitration ever compare this claim with another?"""
        return self.slot is not None


def competence(speaker: str) -> frozenset[str]:
    return COMPETENCE.get(speaker, frozenset())


def assess(memory: Memory) -> Assessment:
    """Trust for this claim, from this writer -- not for this writer.

    An unnameable claim keeps its authority and is flagged instead. Lowering
    it would encode "our vocabulary is incomplete" as "this writer is
    unreliable", which is a different statement about a different party.
    """
    slot = slot_of(memory)
    authority = memory.provenance.authority
    if slot is None:
        return Assessment(memory, slot, Verdict.UNNAMEABLE, authority)
    if slot in competence(memory.provenance.speaker):
        return Assessment(memory, slot, Verdict.COMPETENT, authority)
    return Assessment(memory, slot, Verdict.OUT_OF_DOMAIN, min(authority, OUT_OF_DOMAIN))


def unchecked(memories: list[Memory]) -> list[Memory]:
    """Agent writes that claim no modelled slot.

    These are the ones to look at first. A claim nothing can contradict is
    not a claim that survived scrutiny; it is one that never met any, and the
    store reports the two identically.
    """
    return [
        m
        for m in memories
        if m.provenance.speaker not in ("user", "assistant") and slot_of(m) is None
    ]
