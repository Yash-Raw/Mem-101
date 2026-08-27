"""Written and reachable are different measurements. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

score = _solution.score
score_profiles = _solution.score_profiles


@pytest.fixture(scope="module")
def scores():
    return score_profiles()


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.score([])


def test_both_profiles_score_full_written_recall(scores) -> None:
    """The uncomfortable result: beginner looks perfect on a store-shaped check."""
    assert scores["beginner"].state_recall == 1.0
    assert scores["intermediate"].state_recall == 1.0


def test_and_neither_can_reach_the_employer(scores) -> None:
    for name in ("beginner", "intermediate"):
        assert scores[name].reached["employer"] is None
        assert scores[name].reachability == 0.75


def test_the_employer_state_is_absent_in_one_and_present_in_the_other(scores) -> None:
    """Same reachability, different reason. The ratio hides that; `found` does not."""
    assert scores["beginner"].found["employer"] is True     # "Priya is at Calico now"
    assert scores["intermediate"].found["employer"] is True  # "works at Calico Systems"


def test_over_extraction_goes_to_zero(scores) -> None:
    b, i = scores["beginner"], scores["intermediate"]
    assert len(b.over_extracted) == 3 and round(b.over_extraction_rate, 2) == 0.08
    assert i.over_extracted == [] and i.over_extraction_rate == 0.0


def test_the_diet_states_are_reachable_in_both(scores) -> None:
    for name in ("beginner", "intermediate"):
        reached = scores[name].reached
        assert reached["no meat"] == 1
        assert reached["fish permitted"] == 1
        assert reached["gluten"] is not None


def test_raising_k_reveals_the_difference(scores) -> None:
    """At k=20 the intermediate employer becomes reachable; beginner's does not."""
    wide = score_profiles(k=20)
    assert wide["intermediate"].reached["employer"] == 18
    assert wide["beginner"].reached["employer"] is None
