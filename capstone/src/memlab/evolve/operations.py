"""Turning a named relationship into an operation.

ADD / UPDATE / DELETE / NOOP is the standard vocabulary, and the standard
mistake is letting a model choose from it directly. Asked "what should I do
with these two memories", a model will confidently answer UPDATE for a pair it
misread, overwrite a correct belief, and leave no trace -- the single largest
source of silent memory corruption in this kind of system.

Here the mapping is a lookup table. The model contributed one thing: what the
relationship *is*. Everything after that is policy, and policy belongs in code
you can read, test, and diff.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..types import Memory
from .arbitrate import Verdict, arbitrate
from .conflict import Conflict, Relation


class Operation(str, Enum):
    ADD = "add"        # nothing to reconcile; keep both
    UPDATE = "update"  # one belief retires the other
    MERGE = "merge"    # same claim restated; collapse
    NOOP = "noop"      # compatible; leave alone


# Relationship -> operation. The whole policy, in one readable table.
POLICY: dict[Relation, Operation] = {
    Relation.CONTRADICTION: Operation.UPDATE,
    Relation.REFINEMENT: Operation.UPDATE,   # the narrower claim retires the broader
    Relation.DUPLICATE: Operation.MERGE,
    Relation.COMPATIBLE: Operation.NOOP,
}


@dataclass
class Decision:
    conflict: Conflict
    operation: Operation
    verdict: Verdict | None

    @property
    def retires(self) -> Memory | None:
        return self.verdict.loser if self.operation is Operation.UPDATE else None


def decide(conflict: Conflict, trust=None) -> Decision:
    operation = POLICY[conflict.relation]
    verdict = (
        arbitrate(conflict.a, conflict.b, trust)
        if operation in (Operation.UPDATE, Operation.MERGE)
        else None
    )
    return Decision(conflict=conflict, operation=operation, verdict=verdict)


def decide_all(conflicts: list[Conflict], trust=None) -> list[Decision]:
    return [decide(c, trust) for c in conflicts]
