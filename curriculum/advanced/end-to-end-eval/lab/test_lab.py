"""Six profiles, one battery, three distinguished."""
from __future__ import annotations

from itertools import pairwise

import pytest
from memlab import labkit
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

flat = _solution.flat
regressions = _solution.regressions
run = _solution.run

PRIYA = Scope(user="priya")
PROFILES = ("I4", "I6", "I8", "A1", "A2", "A3")


@pytest.fixture(scope="module")
def rows(tmp_path_factory):
    return run(PROFILES, PRIYA, tmp_path_factory.mktemp("ee"))


def test_stub_is_runnable(tmp_path) -> None:
    with pytest.raises(NotImplementedError):
        _lab.run(("I8",), PRIYA, tmp_path)


def test_every_profile_believes_the_right_thing(rows) -> None:
    assert [r.profile for r in rows] == list(PROFILES)
    assert all(r.belief_exam for r in rows)
    assert all((r.memories, r.live) == (37, 30) for r in rows)


def test_three_component_metrics_never_move(rows) -> None:
    """Already correct at I4; they cannot justify anything after it."""
    for stage in ("extract", "resolve", "arbitrate"):
        assert flat(rows, stage), stage
        assert all(r.get(stage) == 1.0 for r in rows)


def test_only_anchor_moves_and_only_at_a1(rows) -> None:
    by_profile = {r.profile: r.get("anchor") for r in rows}
    assert by_profile["I4"] == by_profile["I6"] == by_profile["I8"] == 0.0
    assert by_profile["A1"] == by_profile["A2"] == by_profile["A3"] == 1.0
    assert not flat(rows, "anchor")


def test_the_budget_captures_i6_and_i8(rows) -> None:
    budgets = {r.profile: r.lowest_budget for r in rows}
    assert budgets["I4"] is None
    assert budgets["I6"] == 77
    assert budgets["I8"] == 51
    assert budgets["A1"] == budgets["A2"] == budgets["A3"] == 51


def test_the_battery_distinguishes_three_of_six(rows) -> None:
    moved = set()
    for earlier, later in pairwise(rows):
        if later.components != earlier.components:
            moved.add(later.profile)
        if later.lowest_budget != earlier.lowest_budget:
            moved.add(later.profile)
    assert moved == {"I6", "I8", "A1"}


def test_no_regressions(rows) -> None:
    """An empty list is the machine saying it looked."""
    assert regressions(rows) == []


def test_a3_is_identical_to_a2(rows) -> None:
    """Every write the corpus contains is legitimate; refusals are not scored."""
    a2 = next(r for r in rows if r.profile == "A2")
    a3 = next(r for r in rows if r.profile == "A3")
    assert (a2.memories, a2.live, a2.lowest_budget) == (
        a3.memories, a3.live, a3.lowest_budget
    )
    assert a2.components == a3.components


def test_sharing_a_store_measures_the_last_profile_six_times(tmp_path) -> None:
    """The stretch: build once with the newest path, score everything against it."""
    from memlab.app.chat import ingest
    from memlab.eval.components import report
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore

    shared = JsonlStore(tmp_path / "shared.jsonl")
    shared.clear()
    ingest(shared, PRIYA, at("A3"))
    memories = shared.all()

    scores = {
        m.stage: m.rate for m in report(memories, PRIYA) if m.scorable
    }
    assert scores["anchor"] == 1.0, "even scored 'as I4', because A3 wrote it"
