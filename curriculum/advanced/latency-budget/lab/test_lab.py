"""The expensive stage is deferrable; the cheap one is the whole budget."""
from __future__ import annotations

import pathlib

import pytest
from memlab import labkit

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

When = _solution.When
budget = _solution.budget
split = _solution.split

EXTRACT_CALLS = 24      # cost-model's 48 completions, minus conflict.classify
CONSOLIDATION_CALLS = 24  # every classify call, all of them deferred
TURNS = 24


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.split()


def test_three_of_seven_stages_block(  ) -> None:
    stages = split()
    assert len(stages) == 7
    blocking = [s.name for s in stages if s.when is When.SYNCHRONOUS]
    assert blocking == ["extract", "resolve", "arbitrate"]


def test_half_the_cost_is_on_the_critical_path() -> None:
    per_turn = budget(EXTRACT_CALLS, CONSOLIDATION_CALLS, TURNS)
    assert per_turn.synchronous == 1.0
    assert per_turn.deferred == 1.0
    assert per_turn.total == 2.0
    assert per_turn.blocking_share == 0.5


def test_conflict_detection_is_a_model_call_and_all_of_it_is_deferred() -> None:
    """0 during the per-turn loop, 24 during consolidation."""
    import tempfile

    import memlab.evolve.conflict as conflict_mod
    from memlab.app.chat import _agent_memories, ingest  # noqa: F401
    from memlab.fixtures import load_turns
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    pipeline = at("A3")
    store = JsonlStore(pathlib.Path(tempfile.mkdtemp()) / "m.jsonl")
    store.clear()
    seen = {"n": 0}
    original = conflict_mod.classify
    conflict_mod.classify = lambda *a, **k: (
        seen.__setitem__("n", seen["n"] + 1), original(*a, **k)
    )[1]
    try:
        for turn in (t for t in load_turns(user_only=True) if t["session"] < 14):
            written = pipeline.extract(turn, scope)
            if pipeline.resolve is not None:
                written = pipeline.resolve(written, store.all())
            store.add(written)
        during = seen["n"]
        store.add(_agent_memories(scope))
        store.replace(pipeline.consolidate(store.all()))
    finally:
        conflict_mod.classify = original

    assert during == 0
    assert seen["n"] - during == 24


def test_the_first_version_reported_eighty_one_percent() -> None:
    """Passing cost-model's total as the extraction count. Internally
    consistent, no test failure, and describing a system that does not exist."""
    wrong = budget(48, 11, TURNS)
    assert round(wrong.blocking_share, 2) == 0.81


def test_extraction_is_the_whole_blocking_cost() -> None:
    """1.0 of 2.0, and deferring it is not an optimisation."""
    per_turn = budget(EXTRACT_CALLS, CONSOLIDATION_CALLS, TURNS)
    assert per_turn.synchronous == per_turn.total - per_turn.deferred


def test_the_deferred_half_is_a_model_call_too() -> None:
    """Consolidation is not the cheap half; it is the half already moved."""
    per_turn = budget(EXTRACT_CALLS, CONSOLIDATION_CALLS, TURNS)
    assert per_turn.deferred == 1.0


def test_every_stage_states_why(  ) -> None:
    for stage in split():
        assert stage.why, stage.name


def test_arbitrate_is_the_only_conditional_entry() -> None:
    """Synchronous by property of the turn, not of the stage."""
    conditional = [s for s in split() if "otherwise deferred" in s.why]
    assert [s.name for s in conditional] == ["arbitrate"]


def test_reflect_is_listed_though_unwired() -> None:
    """A budget that omits what you decided not to run will regain it."""
    reflect = next(s for s in split() if s.name == "reflect")
    assert reflect.when is When.DEFERRED
    assert "unwired" in reflect.why


def test_a_zero_turn_budget_does_not_divide_by_zero() -> None:
    assert budget(0, 0, 1).blocking_share == 0.0
