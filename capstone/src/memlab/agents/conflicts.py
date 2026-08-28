"""What happens when two writers claim the same attribute.

The corpus is thin here on purpose, and measuring it first is what stops this
lesson inventing a problem. Conflict candidates over the unconsolidated store:

    27 candidate pairs
       agent vs user   1     the relocation rumour against the address
       agent vs agent  0

One cross-writer conflict, and I4 already gets it right: the travel agent
arrives at authority 0.3, `arbitrate`'s first rule sees a relayed claim
against a first-party one, and the address wins whatever the dates say.

That defence is a **cliff, not a slope**. `FIRST_PARTY` is a threshold at 0.5,
so 0.9 and 1.0 are the same number to it -- and rule 1 stops discriminating
the moment both writers are above the line:

    user says "pescatarian" (2025-08-02, authority 1.0)
    calendar agent says "vegetarian" (2026-06-01, authority 0.9)

    by authority   rule=recency     winner=calendar-agent
    by trust       rule=authority   winner=the user

An agent trusted for scheduling overwrites the user's own dietary belief by
being newer. Scoring the *claim* -- out of domain, so 0.3 -- puts it back
below the line and rule 1 discriminates again.

On this corpus the substitution changes nothing: the one real cross-writer
pair is a 0.3 relay whose out-of-domain discount lands exactly on its existing
authority. `@A3` is byte-identical to `@A2`. The mechanism is right and this
corpus cannot show it, which is worth saying rather than staging.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..evolve.arbitrate import FIRST_PARTY, arbitrate
from ..evolve.conflict import candidates
from ..types import Memory, Scope
from .trust import claim_trust


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
