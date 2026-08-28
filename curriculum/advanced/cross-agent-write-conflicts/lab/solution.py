"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass

from memlab.agents.trust import claim_trust
from memlab.evolve.arbitrate import FIRST_PARTY, arbitrate
from memlab.evolve.conflict import candidates
from memlab.types import Memory, Scope


@dataclass(frozen=True)
class CrossWriter:
    """A candidate pair whose two memories came from different writers."""

    a: Memory
    b: Memory
    slot: str

    @property
    def writers(self) -> tuple[str, str]:
        return (self.a.provenance.speaker, self.b.provenance.speaker)

    @property
    def agent_versus_agent(self) -> bool:
        return bool(self.a.scope.agent) and bool(self.b.scope.agent)


def cross_writer(memories: list[Memory], scope: Scope) -> list[CrossWriter]:
    """Candidate pairs where the two claims have different authors.

    Run this over the *unconsolidated* store. After reconciliation the losers
    are retired and excluded from candidate generation, so the same call
    returns nothing and the absence looks like a property of the corpus rather
    than of when you asked.
    """
    return [
        CrossWriter(a=a, b=b, slot=slot)
        for a, b, slot in candidates(memories, scope)
        if a.provenance.speaker != b.provenance.speaker
    ]


def decided_by(a: Memory, b: Memory) -> tuple[str, str, str, str]:
    """The rule and winner under raw authority, then under per-claim trust."""
    by_authority = arbitrate(a, b)
    by_trust = arbitrate(a, b, claim_trust)
    return (
        by_authority.rule,
        by_authority.winner.provenance.speaker,
        by_trust.rule,
        by_trust.winner.provenance.speaker,
    )


def above_the_line(memory: Memory) -> bool:
    """Whether rule 1 will treat this writer as first-party at all."""
    return memory.provenance.authority >= FIRST_PARTY
