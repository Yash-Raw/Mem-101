"""Retiring a belief without destroying it.

This is the mechanism the whole course has been building toward, and it is
about forty lines. `invalid_at` marks when a belief stopped being true;
`superseded_by` records what replaced it. Nothing is deleted.

That distinction is what keeps "where do I work?" and "where did I work before
Calico?" both answerable, and it is why `Memory.supersede` returns a new record
rather than mutating one -- the audit trail is the point.

Note what it does NOT touch: episodes. "Priya is leaving Northwind Labs"
remains permanently true, and `typed-memory-model` is what makes that
structural rather than a special case.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..types import Memory, Scope
from .conflict import detect
from .operations import Decision, Operation, decide_all
from .promote import corroborate


@dataclass
class Reconciliation:
    memories: list[Memory]
    decisions: list[Decision]

    @property
    def retired(self) -> list[Memory]:
        return [m for m in self.memories if not m.is_live]

    def summary(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for d in self.decisions:
            out[d.operation.value] = out.get(d.operation.value, 0) + 1
        return out


def _when(memory: Memory) -> datetime:
    """Event time: when the fact this memory states became true."""
    return memory.happened_at or memory.recorded_at


def _found_out(loser: Memory, winner: Memory) -> datetime:
    """Belief time: the first moment the store could have known to retire it.

    Not the winner's event time. The Berlin hearsay is retired on the date
    Priya gave her address -- nine months before the claim was written -- so
    the record says the store stopped believing something it had not yet been
    told. A belief cannot end before it begins.
    """
    return max(loser.recorded_at, winner.recorded_at)


def reconcile(
    memories: list[Memory], scope: Scope, bitemporal: bool = False, trust=None
) -> Reconciliation:
    """Detect, decide, and apply -- retiring losers, corroborating restatements.

    `bitemporal` (A1) splits the one retirement instant into two: `valid_to`
    for when the fact stopped being true, `invalid_at` for when the store
    found out. Off, both get the winner's event time -- which is what every
    Level 2 figure was measured against.
    """
    decisions = decide_all(detect(memories, scope), trust)

    retire: dict[str, tuple[str, datetime, datetime]] = {}
    support: dict[str, list[Memory]] = {}

    for d in decisions:
        if d.operation is Operation.UPDATE and d.verdict:
            loser, winner = d.verdict.loser, d.verdict.winner
            # The fact stopped being true when its replacement became true;
            # the store stopped believing it when it had both in hand.
            retire[loser.id] = (
                winner.id,
                _when(winner),
                _found_out(loser, winner) if bitemporal else _when(winner),
            )
        elif d.operation is Operation.MERGE and d.verdict:
            # A merge that leaves both copies live is not a merge. Retire the
            # loser and corroborate the winner -- one fact, one live record,
            # and the restatement preserved as evidence.
            support.setdefault(d.verdict.winner.id, []).append(d.verdict.loser)
            retire[d.verdict.loser.id] = (
                d.verdict.winner.id,
                _when(d.verdict.winner),
                _found_out(d.verdict.loser, d.verdict.winner)
                if bitemporal
                else _when(d.verdict.winner),
            )

    out = []
    for memory in memories:
        if memory.id in retire:
            by, at, found_out = retire[memory.id]
            memory = memory.supersede(
                by=by, at=at, found_out=found_out, event_end=bitemporal
            )
        elif memory.id in support:
            memory = corroborate(memory, support[memory.id])
        out.append(memory)

    return Reconciliation(memories=out, decisions=decisions)
