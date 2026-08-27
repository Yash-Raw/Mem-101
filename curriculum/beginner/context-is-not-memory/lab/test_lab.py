"""Truncation systematically favours stale facts. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.assemble.simple import estimate_tokens
from memlab.fixtures import load_turns

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

fit_to_budget = _solution.fit_to_budget

BUDGET = 250


def kept_text(newest_first: bool) -> str:
    return " ".join(t["text"] for t in fit_to_budget(load_turns(user_only=True), BUDGET, newest_first))


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.fit_to_budget(load_turns(user_only=True), 250)


def test_the_whole_history_would_fit_in_a_modern_window() -> None:
    """The shortcut is not obviously wrong. That is why it needs refuting."""
    total = sum(estimate_tokens(t["text"]) for t in load_turns(user_only=True))
    assert total < 3000


def test_the_budget_is_respected_and_turns_are_never_split() -> None:
    turns = load_turns(user_only=True)
    kept = fit_to_budget(turns, BUDGET)
    assert sum(estimate_tokens(t["text"]) for t in kept) <= BUDGET
    assert all(t in turns for t in kept), "whole turns only"
    assert [t["ts"] for t in kept] == sorted(t["ts"] for t in kept), "returned in order"


def test_oldest_first_keeps_the_stale_employer_and_drops_the_change() -> None:
    text = kept_text(newest_first=False)
    assert "Northwind Labs" in text
    assert "Calico Systems" not in text, "the job change falls off the edge"
    assert "gluten" not in text, "and so does every later diet update"


def test_newest_first_inverts_the_result_exactly() -> None:
    text = kept_text(newest_first=True)
    assert "Calico Systems" in text
    assert "gluten" in text
    assert "vegetarian" not in text, "the diet baseline is now what falls off"


def test_a_bigger_budget_exposes_the_contradiction_it_was_hiding() -> None:
    """At 400, oldest-first keeps BOTH employers and no way to choose."""
    turns = load_turns(user_only=True)
    text = " ".join(t["text"] for t in fit_to_budget(turns, 400))
    assert "Northwind Labs" in text and "Calico Systems" in text


def test_no_ordering_keeps_everything_that_matters() -> None:
    """The point of the lab, stated as a test."""
    for newest_first in (False, True):
        text = kept_text(newest_first)
        complete = "Calico Systems" in text and "vegetarian" in text
        assert not complete, "no fixed ordering preserves both; selection must be query-driven"
