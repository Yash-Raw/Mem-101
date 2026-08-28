"""One judgement, three protections, and a rule about arbitration."""
from __future__ import annotations

import json
import pathlib

import pytest
from memlab import labkit

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Role = _solution.Role
arbitration_is_never_a_model = _solution.arbitration_is_never_a_model
judging_the_exam = _solution.judging_the_exam
uses = _solution.uses

ROOT = pathlib.Path(__file__).resolve().parents[4]


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.uses()


def test_exactly_one_call_is_a_judgement() -> None:
    calls = uses()
    assert len(calls) == 3
    judgements = [u for u in calls if u.role is Role.JUDGEMENT]
    assert len(judgements) == 1
    assert judgements[0].site == "evolve/conflict.py"


def test_the_judgement_has_all_three_protections() -> None:
    judge = next(u for u in uses() if u.role is Role.JUDGEMENT)
    assert judge.bounded_output
    assert judge.checked_against_gold
    assert judge.reproducible
    assert judge.safe


def test_safe_is_an_and_not_a_score() -> None:
    """Remove any one and the others stop helping."""
    judge = next(u for u in uses() if u.role is Role.JUDGEMENT)
    for field in ("bounded_output", "checked_against_gold", "reproducible"):
        weakened = judge.__class__(
            **{**judge.__dict__, field: False}
        )
        assert not weakened.safe, field


def test_generation_sites_are_unsafe_and_that_is_fine() -> None:
    """Unbounded and unscored -- and nothing downstream trusts them."""
    generations = [u for u in uses() if u.role is Role.GENERATION]
    assert len(generations) == 2
    assert all(not u.safe for u in generations)
    assert all(u.reproducible for u in generations)


def test_the_model_is_called_in_exactly_three_files() -> None:
    """The table is a claim about the source; check it."""
    src = ROOT / "capstone" / "src" / "memlab"
    calling = sorted(
        str(p.relative_to(src))
        for p in src.rglob("*.py")
        if "client.complete(" in p.read_text()
    )
    assert calling == sorted(u.site for u in uses())


def test_arbitration_is_a_rule_about_state() -> None:
    text = arbitration_is_never_a_model()
    assert "must not" in text
    assert "explainable" in text


def test_the_exam_is_backed_by_seventy_five_fixtures() -> None:
    count = len(
        json.loads((ROOT / "capstone" / "fixtures" / "llm_responses.json").read_text())
    )
    assert count == 75
    assert str(count) in judging_the_exam(count)


def test_arbitrate_calls_no_model() -> None:
    """The rule, checked against the file it is about."""
    source = (ROOT / "capstone" / "src" / "memlab" / "evolve" / "arbitrate.py").read_text()
    assert "client.complete" not in source
    assert "rule" in source
