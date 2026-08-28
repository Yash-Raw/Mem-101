"""The expensive stage is deferrable; the cheap one is the whole budget."""
from __future__ import annotations

import pytest
from memlab import labkit

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

When = _solution.When
budget = _solution.budget
split = _solution.split

EXTRACT_CALLS = 48
CONSOLIDATIONS = 11
TURNS = 24


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.split()


def test_three_of_seven_stages_block(  ) -> None:
    stages = split()
    assert len(stages) == 7
    blocking = [s.name for s in stages if s.when is When.SYNCHRONOUS]
    assert blocking == ["extract", "resolve", "arbitrate"]


def test_eighty_one_percent_of_the_cost_is_on_the_critical_path() -> None:
    per_turn = budget(EXTRACT_CALLS, CONSOLIDATIONS, TURNS)
    assert per_turn.synchronous == 2.0
    assert per_turn.deferred == 0.46
    assert per_turn.total == 2.46
    assert round(per_turn.blocking_share, 2) == 0.81


def test_extraction_is_the_whole_blocking_cost() -> None:
    """2.0 of 2.46, and deferring it is not an optimisation."""
    per_turn = budget(EXTRACT_CALLS, CONSOLIDATIONS, TURNS)
    assert per_turn.synchronous > per_turn.deferred * 4


def test_the_gate_costs_less_than_half_a_call_per_turn() -> None:
    """sleep-time-compute's 11 of 24, priced."""
    per_turn = budget(EXTRACT_CALLS, CONSOLIDATIONS, TURNS)
    assert per_turn.deferred == round(CONSOLIDATIONS / TURNS, 2)


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
