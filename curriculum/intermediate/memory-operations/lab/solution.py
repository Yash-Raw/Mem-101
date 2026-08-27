"""Reference solution."""
from __future__ import annotations

from memlab.evolve.arbitrate import arbitrate
from memlab.evolve.conflict import Conflict, Relation
from memlab.evolve.operations import Decision, Operation

POLICY: dict[Relation, Operation] = {
    Relation.CONTRADICTION: Operation.UPDATE,
    Relation.REFINEMENT: Operation.UPDATE,
    Relation.DUPLICATE: Operation.MERGE,
    Relation.COMPATIBLE: Operation.NOOP,
}


def decide(conflict: Conflict) -> Decision:
    operation = POLICY[conflict.relation]
    verdict = (
        arbitrate(conflict.a, conflict.b)
        if operation in (Operation.UPDATE, Operation.MERGE)
        else None
    )
    return Decision(conflict=conflict, operation=operation, verdict=verdict)


def decide_all(conflicts: list[Conflict]) -> list[Decision]:
    return [decide(c) for c in conflicts]


def policy_is_exhaustive() -> bool:
    return set(POLICY) == set(Relation)
