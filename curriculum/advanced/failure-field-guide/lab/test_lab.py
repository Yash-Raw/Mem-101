"""Seven symptoms, five ambiguous, all seven observed."""
from __future__ import annotations

import pathlib

import pytest
from memlab import labkit

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

ambiguous = _solution.ambiguous
coverage = _solution.coverage
field_guide = _solution.field_guide

CURRICULUM = pathlib.Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def failures():
    return field_guide()


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.field_guide()


def test_seven_symptoms_five_ambiguous(failures) -> None:
    assert len(failures) == 7
    assert len(ambiguous(failures)) == 5


def test_every_entry_was_measured(failures) -> None:
    assert coverage(failures) == (7, 7)


def test_every_cited_lesson_exists(failures) -> None:
    """A guide of things that happened, checkable against the course."""
    levels = ("beginner", "intermediate", "advanced")
    for failure in failures:
        for lesson in failure.met_in.split(", "):
            assert any(
                (CURRICULUM / level / lesson / "index.md").exists()
                for level in levels
            ), lesson


def test_every_entry_names_a_measurement(failures) -> None:
    """The tell is the column that does the work."""
    for failure in failures:
        assert failure.distinguish
        assert failure.distinguish != failure.symptom


def test_the_three_cause_symptom_is_ordered(failures) -> None:
    """Store, then slot, then pool -- each answer makes the next meaningful."""
    recall = next(f for f in failures if "never recalled" in f.symptom)
    assert len(recall.causes) == 3
    tell = recall.distinguish
    assert tell.index("store") < tell.index("slot_of") < tell.index("eligible")


def test_two_symptoms_have_a_single_cause(failures) -> None:
    """Where the tell is conclusive, which is worth as much."""
    single = [f for f in failures if not f.ambiguous]
    assert len(single) == 2
    assert any("retrievable" in f.symptom for f in single)
    assert any("batch" in f.symptom for f in single)


def test_no_symptom_names_a_stage(failures) -> None:
    """Indexed by the question, not by the answer."""
    stages = ("extract", "consolidat", "rank", "assemble", "decay")
    for failure in failures:
        assert not any(s in failure.symptom.lower() for s in stages), failure.symptom
