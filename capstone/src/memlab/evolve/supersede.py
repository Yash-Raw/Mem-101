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
    return memory.happened_at or memory.recorded_at


def reconcile(memories: list[Memory], scope: Scope) -> Reconciliation:
    """Detect, decide, and apply -- retiring losers, corroborating restatements."""
    decisions = decide_all(detect(memories, scope))

    retire: dict[str, tuple[str, datetime]] = {}
    support: dict[str, list[Memory]] = {}

    for d in decisions:
        if d.operation is Operation.UPDATE and d.verdict:
            loser, winner = d.verdict.loser, d.verdict.winner
            # A belief is invalid from the moment its replacement became true.
            retire[loser.id] = (winner.id, _when(winner))
        elif d.operation is Operation.MERGE and d.verdict:
            # A merge that leaves both copies live is not a merge. Retire the
            # loser and corroborate the winner -- one fact, one live record,
            # and the restatement preserved as evidence.
            support.setdefault(d.verdict.winner.id, []).append(d.verdict.loser)
            retire[d.verdict.loser.id] = (d.verdict.winner.id, _when(d.verdict.winner))

    out = []
    for memory in memories:
        if memory.id in retire:
            by, at = retire[memory.id]
            memory = memory.supersede(by=by, at=at)
        elif memory.id in support:
            memory = corroborate(memory, support[memory.id])
        out.append(memory)

    return Reconciliation(memories=out, decisions=decisions)
