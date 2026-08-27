"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from memlab.evolve.conflict import detect
from memlab.evolve.operations import Decision, Operation, decide_all
from memlab.evolve.promote import corroborate
from memlab.types import Memory, Scope


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
            support.setdefault(d.verdict.winner.id, []).append(d.verdict.loser)

    out = []
    for memory in memories:
        if memory.id in retire:
            by, at = retire[memory.id]
            memory = memory.supersede(by=by, at=at)
        elif memory.id in support:
            memory = corroborate(memory, support[memory.id])
        out.append(memory)

    return Reconciliation(memories=out, decisions=decisions)


def reconcile_by_deleting(memories: list[Memory], scope: Scope) -> list[Memory]:
    """The wrong way, for contrast.

    Passes the exam. Loses the history, the audit trail, and any chance of
    recovering from a misclassification.
    """
    from memlab.evolve.conflict import detect
    from memlab.evolve.operations import Operation, decide_all

    doomed = {
        d.verdict.loser.id
        for d in decide_all(detect(memories, scope))
        if d.operation is Operation.UPDATE and d.verdict
    }
    return [m for m in memories if m.id not in doomed]
