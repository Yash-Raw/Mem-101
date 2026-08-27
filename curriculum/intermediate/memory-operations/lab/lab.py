"""Lab: policy belongs in a table.

    uv run python curriculum/intermediate/memory-operations/lab/lab.py
"""
from __future__ import annotations

from memlab.evolve.conflict import Conflict, Relation
from memlab.evolve.operations import Decision, Operation

# TODO: map every Relation to the Operation it implies.
#   contradiction -> one belief retires the other
#   refinement    -> the narrower retires the broader (same operation, different
#                    consequences -- compatible parts of the old belief survive)
#   duplicate     -> collapse and corroborate
#   compatible    -> leave both alone
# Note what is absent: DELETE. Nothing in belief updating deletes.
POLICY: dict[Relation, Operation] = {}


def decide(conflict: Conflict) -> Decision:
    """TODO: look up the operation, and arbitrate only where one is needed."""
    raise NotImplementedError("implement decide")


def decide_all(conflicts: list[Conflict]) -> list[Decision]:
    return [decide(c) for c in conflicts]


def policy_is_exhaustive() -> bool:
    return set(POLICY) == set(Relation)


def main() -> None:
    from collections import Counter

    from memlab.app.chat import ingest
    from memlab.evolve.conflict import detect
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-ops.jsonl")
    store.clear()
    ingest(store, scope, at("I3"))

    decisions = decide_all(detect(store.all(), scope))
    print("operations:", dict(Counter(d.operation.value for d in decisions)))
    print(f"policy is exhaustive: {policy_is_exhaustive()}\n")

    for d in decisions:
        if d.operation is Operation.UPDATE and d.verdict:
            print(f"  UPDATE [{d.conflict.relation.value:<13}] via {d.verdict.rule}")
            print(f"     keep    {d.verdict.winner.content[:56]}")
            print(f"     retire  {d.verdict.loser.content[:56]}")


if __name__ == "__main__":
    main()
