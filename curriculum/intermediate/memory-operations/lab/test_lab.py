"""The model names the relation; the table decides. Asserted."""
from __future__ import annotations

from collections import Counter

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.evolve.conflict import Relation, detect
from memlab.evolve.operations import Operation
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

POLICY = _solution.POLICY
decide_all = _solution.decide_all
policy_is_exhaustive = _solution.policy_is_exhaustive

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def decisions(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("ops") / "m.jsonl")
    ingest(store, PRIYA, at("I3"))
    return decide_all(detect(store.all(), PRIYA))


def test_stub_is_runnable() -> None:
    assert _lab.POLICY == {}, "the table starts empty"


def test_the_policy_is_exhaustive() -> None:
    """A new relation with no entry must fail loudly, not be ignored."""
    assert policy_is_exhaustive()


def test_delete_is_not_in_the_vocabulary() -> None:
    """Nothing in belief updating deletes. Erasure is a governance operation."""
    assert not hasattr(Operation, "DELETE")
    assert "delete" not in {op.value for op in Operation}
    assert "delete" not in {op.value for op in POLICY.values()}


def test_the_breakdown(decisions) -> None:
    counts = Counter(d.operation.value for d in decisions)
    assert counts == {"noop": 15, "update": 8, "merge": 1}


def test_two_thirds_of_correct_reconciliation_is_doing_nothing(decisions) -> None:
    noops = sum(1 for d in decisions if d.operation is Operation.NOOP)
    assert noops / len(decisions) > 0.6


def test_both_change_relations_map_to_update() -> None:
    assert POLICY[Relation.CONTRADICTION] is Operation.UPDATE
    assert POLICY[Relation.REFINEMENT] is Operation.UPDATE


def test_every_update_records_why(decisions) -> None:
    """A decision that cannot explain itself is indistinguishable from a bug."""
    for d in decisions:
        if d.operation is Operation.UPDATE:
            assert d.verdict is not None
            assert d.verdict.rule
            assert d.retires is d.verdict.loser
        else:
            assert d.retires is None


def test_the_relation_survives_the_mapping(decisions) -> None:
    """Contradiction and refinement share an operation and differ in the record."""
    relations = {d.conflict.relation for d in decisions if d.operation is Operation.UPDATE}
    assert relations == {Relation.CONTRADICTION, Relation.REFINEMENT}


def test_deciding_is_deterministic(decisions, tmp_path) -> None:
    store = JsonlStore(tmp_path / "m.jsonl")
    ingest(store, PRIYA, at("I3"))
    again = decide_all(detect(store.all(), PRIYA))
    assert [d.operation for d in again] == [d.operation for d in decisions]
