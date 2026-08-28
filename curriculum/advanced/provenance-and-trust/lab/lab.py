"""Lab: trust the claim, not the claimant.

    uv run python curriculum/advanced/provenance-and-trust/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from memlab.evolve.conflict import SLOTS
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
    raise NotImplementedError("implement assess")


def unchecked(memories: list[Memory]) -> list[Memory]:
    """Agent writes that claim no modelled slot.

    These are the ones to look at first. A claim nothing can contradict is
    not a claim that survived scrutiny; it is one that never met any, and the
    store reports the two identically.
    """
    raise NotImplementedError("implement unchecked")


def main() -> None:
    from collections import Counter

    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-trust.jsonl")
    store.clear()
    ingest(store, scope, at("A3"))
    memories = store.all()
    agent_writes = [m for m in memories if m.scope.agent]

    print(f"   {'writer':16}{'auth':>6}{'slot':>12}{'verdict':>16}"
          f"{'trust':>7}{'checkable':>11}")
    for m in agent_writes:
        a = assess(m)
        print(f"   {m.provenance.speaker:16}{m.provenance.authority:>6}"
              f"{a.slot!s:>12}{a.verdict.value:>16}{a.trust:>7}"
              f"{a.checkable!s:>11}")

    missed = unchecked(memories)
    print(f"\n   agent writes nothing can contradict: "
          f"{len(missed)} of {len(agent_writes)}")
    for m in missed:
        print(f"      {m.content}")

    counts = Counter(assess(m).verdict.value for m in memories)
    print(f"\n   all {len(memories)}, by verdict:\n")
    for verdict in ("competent", "unnameable", "out of domain"):
        print(f"   {verdict:16}{counts[verdict]:>4}")

    users_own = [
        m for m in memories
        if m.provenance.speaker == "user" and assess(m).verdict.value == "unnameable"
    ]
    print(f"\n   ...of which the user's own: {len(users_own)}")
    for m in users_own[:2]:
        print(f"      {m.content}")

    consulted = {
        assess(m).slot for m in agent_writes if assess(m).verdict.value != "unnameable"
    }
    print(f"\n   competence entries actually consulted on this corpus: "
          f"{sorted(c for c in consulted if c)}")


if __name__ == "__main__":
    main()
