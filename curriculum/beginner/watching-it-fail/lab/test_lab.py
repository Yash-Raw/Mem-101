"""The catalogue, and the exam. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

diagnose = _solution.diagnose
wrong_answers = _solution.wrong_answers

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("diag") / "m.jsonl")
    ingest(store, PRIYA)
    return store.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.diagnose(memories, PRIYA)


def test_all_seven_are_found(memories) -> None:
    findings = diagnose(memories, PRIYA)
    assert [f.n for f in findings] == [1, 2, 3, 4, 5, 6, 7]


def test_every_finding_names_the_lesson_that_fixes_it(memories) -> None:
    """A failure without a route out is a complaint."""
    for f in diagnose(memories, PRIYA):
        assert f.fixed_by and "-" in f.fixed_by


def test_findings_carry_measured_evidence(memories) -> None:
    """Not descriptions. Numbers from this store."""
    for f in diagnose(memories, PRIYA):
        assert any(ch.isdigit() for ch in f.evidence), f"finding {f.n} has no measurement"


def test_the_dead_employer_outranks_the_live_one(memories) -> None:
    stale = next(f for f in diagnose(memories, PRIYA) if f.n == 1)
    assert "ranks 9 of 36" in stale.evidence
    assert "ranks 35" in stale.evidence


def test_nothing_can_ever_be_forgotten(memories) -> None:
    f6 = next(f for f in diagnose(memories, PRIYA) if f.n == 6)
    assert "[0.5]" in f6.evidence and "[0]" in f6.evidence


def test_the_deletion_request_was_filed_not_honoured(memories) -> None:
    """The one failure that is compliance rather than quality."""
    f7 = next(f for f in diagnose(memories, PRIYA) if f.n == 7)
    assert "1 memory records the deletion request" in f7.evidence
    assert "2 PII memories remain" in f7.evidence


def test_the_exam_is_failed_in_a_documented_way(memories) -> None:
    wrong = wrong_answers(memories, PRIYA, k=10)
    assert wrong, "the naive system should fail the session-14 question"
    assert any("Northwind" in w for w in wrong)
