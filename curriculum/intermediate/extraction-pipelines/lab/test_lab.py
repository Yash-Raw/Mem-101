"""Extraction is necessary and not sufficient. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.fixtures import session
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

compare_profiles = _solution.compare_profiles
extract = _solution.extract

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def reports():
    return {r.name: r for r in compare_profiles()}


def test_stub_is_runnable() -> None:
    turn = next(t for t in session(8) if t["role"] == "user")
    with pytest.raises(NotImplementedError):
        _lab.extract(turn, PRIYA)


def test_the_change_now_yields_a_state(reports) -> None:
    """The one paragraph, doing its job."""
    memories = extract(next(t for t in session(8) if t["role"] == "user"), PRIYA)
    contents = [m.content for m in memories]
    assert "Priya works at Calico Systems" in contents
    states = [m for m in memories if m.type is MemoryType.SEMANTIC]
    events = [m for m in memories if m.type is MemoryType.EPISODIC]
    assert states and events, "both the event and the state it produced"


def test_the_gate_drops_transient_activities(reports) -> None:
    beginner, intermediate = reports["beginner"], reports["intermediate"]
    assert beginner.by_type["episodic"] == 12
    assert intermediate.by_type["episodic"] == 9


def test_the_store_shifts_from_events_to_states(reports) -> None:
    b, i = reports["beginner"], reports["intermediate"]
    assert (b.total, b.by_type["semantic"]) == (36, 22)
    assert (i.total, i.by_type["semantic"]) == (38, 27)


def test_the_employer_state_goes_from_absent_to_rank_18(reports) -> None:
    """18 is quoted in this lesson's prose, so it is pinned FOR THIS MODULE.

    Unlike the Beginner figures, it is not a permanent invariant: a later
    module that legitimately changes the intermediate store may move it, and
    must then re-quote it in the prose. Beginner pins may never move at all.
    """
    assert reports["beginner"].calico_state_rank is None
    assert reports["intermediate"].calico_state_rank == 18


def test_but_the_exam_still_fails(reports) -> None:
    """The honest half of the lesson. Fixed in supersession-not-deletion.

    Asserts the RELATIONSHIP, not the ranks. I2 changes store composition, I3
    shrinks it and I4 retires things -- every one legitimately moves these
    integers, and pinning them here would train the habit of "updating the
    number", which is exactly what the Beginner pins exist to forbid.
    """
    for name in ("beginner", "intermediate"):
        assert reports[name].exam_employer == "Northwind Labs"

    i = reports["intermediate"]
    assert i.northwind_rank is not None
    assert i.calico_state_rank > i.northwind_rank, (
        "the dead fact still outranks the live one for 'where do I work?'"
    )


def test_extraction_makes_exactly_one_model_call_per_turn(monkeypatch) -> None:
    """The design commitment that keeps fixtures hand-authorable."""
    from memlab.llm import fake

    calls = []
    original = fake.FakeLLM.complete

    def counted(self, messages, schema=None):
        calls.append(1)
        return original(self, messages, schema)

    monkeypatch.setattr(fake.FakeLLM, "complete", counted)
    extract(next(t for t in session(8) if t["role"] == "user"), PRIYA)
    assert len(calls) == 1
