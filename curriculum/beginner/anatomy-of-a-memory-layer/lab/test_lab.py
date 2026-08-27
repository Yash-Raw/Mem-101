"""Which box lost the answer? Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.fixtures import session
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

populate_except = _solution.populate_except
trace = _solution.trace

QUESTION = "where do I work and what should I not eat?"


def trace_session(n: int, tmp_path) -> object:
    store = JsonlStore(tmp_path / f"s{n}.jsonl")
    scope = Scope(user="priya")
    populate_except(store, scope, skip_session=n)
    turn = next(t for t in session(n) if t["role"] == "user")
    return trace(turn, store, scope, QUESTION)


def test_stub_is_runnable(tmp_path) -> None:
    turn = next(t for t in session(8) if t["role"] == "user")
    with pytest.raises(NotImplementedError):
        _lab.trace(turn, JsonlStore(tmp_path / "x.jsonl"), Scope(user="priya"), QUESTION)


def test_every_box_reports(tmp_path) -> None:
    t = trace_session(8, tmp_path)
    assert [s.box for s in t.stages] == [
        "capture", "extract", "resolve", "store", "retrieve", "assemble"
    ]


def test_extract_produces_no_employer_fact(tmp_path) -> None:
    """The box where the answer was actually lost."""
    memories = trace_session(8, tmp_path).by_box("extract").produced
    assert len(memories) == 2
    assert all(m.type is MemoryType.EPISODIC for m in memories), (
        "the job change became two events; no semantic `employer` fact exists"
    )


def test_resolve_is_a_declared_no_op(tmp_path) -> None:
    """It is not that resolve failed. Beginner has no resolve."""
    stage = trace_session(8, tmp_path).by_box("resolve")
    assert "0 resolved" in stage.note


def test_the_job_change_never_reaches_the_context(tmp_path) -> None:
    t = trace_session(8, tmp_path)
    assert "0 of 2 survived" in t.by_box("assemble").note


def test_the_gluten_fact_survives_the_same_pipeline(tmp_path) -> None:
    """Same pipeline, different phrasing, opposite outcome."""
    t = trace_session(12, tmp_path)
    memories = t.by_box("extract").produced
    assert any(m.type is MemoryType.SEMANTIC for m in memories), "a state, not just an event"
    assert "0 of" not in t.by_box("assemble").note, "it reaches the assembled context"
