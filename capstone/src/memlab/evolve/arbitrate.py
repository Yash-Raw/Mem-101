"""Deciding which belief survives -- with rules, not a model.

Detection is a language judgement, so a model does it. Arbitration is a policy
decision, and handing it to a model is how memory quietly corrupts: the same
pair can be decided differently on two runs, nothing records why, and the
reasoning cannot be audited when a user asks "why do you think that?".

So the model says *these two disagree* and rules say *this one wins*, in a
fixed order, each with a stated reason.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..types import Memory

# Below this, a claim is hearsay and loses to a first-party statement whatever
# its date. Priya's colleague speculating that she is relocating does not beat
# Priya's own address.
FIRST_PARTY = 0.5


@dataclass
class Verdict:
    winner: Memory
    loser: Memory
    rule: str

    @property
    def reason(self) -> str:
        return f"{self.rule}: kept {self.winner.content!r}"


def _when(memory: Memory):
    return memory.happened_at or memory.recorded_at


def arbitrate(a: Memory, b: Memory) -> Verdict:
    """Rules in priority order. The first that discriminates decides."""
    # 1. Authority. A relayed claim never beats a first-party one.
    a_first = a.provenance.authority >= FIRST_PARTY
    b_first = b.provenance.authority >= FIRST_PARTY
    if a_first != b_first:
        winner, loser = (a, b) if a_first else (b, a)
        return Verdict(winner, loser, "authority")

    # 2. Recency, by EVENT time -- when the fact was true, not when it was
    #    learned. Session 11 reports a 2025 commute change in 2026; ingestion
    #    order would get that backwards.
    if _when(a) != _when(b):
        winner, loser = (a, b) if _when(a) > _when(b) else (b, a)
        return Verdict(winner, loser, "recency")

    # 3. Confidence, as a tiebreak within the same moment.
    if a.confidence != b.confidence:
        winner, loser = (a, b) if a.confidence > b.confidence else (b, a)
        return Verdict(winner, loser, "confidence")

    # 4. Deterministic fallback, so the same input always gives the same answer.
    winner, loser = sorted((a, b), key=lambda m: m.id)
    return Verdict(winner, loser, "stable-tiebreak")
