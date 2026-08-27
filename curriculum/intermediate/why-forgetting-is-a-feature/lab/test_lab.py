"""The cost is per-query, not per-byte. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ask, ingest
from memlab.eval.exam import QUESTION
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

audit_context = _solution.audit_context
projected_growth = _solution.projected_growth
tier_census = _solution.tier_census

PRIYA = Scope(user="priya")


def audit_at(profile: str, tmp_path, k: int = 5):
    pipeline = at(profile)
    store = JsonlStore(tmp_path / f"{profile}.jsonl")
    ingest(store, PRIYA, pipeline)
    _, hits = ask(store, PRIYA, QUESTION, k=k, pipeline=pipeline)
    return audit_context(hits, k, store.all()), store


def test_stub_is_runnable(tmp_path) -> None:
    with pytest.raises(NotImplementedError):
        _lab.audit_context([], 5, [])


def test_three_of_five_slots_are_wasted(tmp_path) -> None:
    audit, _ = audit_at("I4", tmp_path)
    assert (audit.useful, audit.slots) == (2, 5)
    assert audit.waste == pytest.approx(0.6)


def test_the_employer_is_not_among_them(tmp_path) -> None:
    """The answer the whole course is about does not reach the model."""
    audit, _ = audit_at("I4", tmp_path)
    assert not any("Calico" in c for c in audit.wasted_contents)


def test_scoring_salience_does_not_change_the_waste(tmp_path) -> None:
    """I5 tiers the store; retrieval does not act on tiers until I6."""
    i4, _ = audit_at("I4", tmp_path)
    i5, _ = audit_at("I5", tmp_path)
    assert (i5.useful, i5.slots) == (i4.useful, i4.slots)


def test_but_the_store_is_now_tiered(tmp_path) -> None:
    _, i4_store = audit_at("I4", tmp_path)
    _, i5_store = audit_at("I5", tmp_path)
    assert tier_census(i4_store.all()) == {"scratch": 0, "working": 30, "long_term": 0}
    census = tier_census(i5_store.all())
    assert census["long_term"] > 0 and census["scratch"] > 0


def test_raising_k_buys_the_answer_by_paying_for_noise(tmp_path) -> None:
    narrow, _ = audit_at("I4", tmp_path, k=5)
    wide, _ = audit_at("I4", tmp_path, k=20)
    assert wide.waste > narrow.waste, "more slots, worse ratio"


def test_growth_at_this_rate(tmp_path) -> None:
    _, store = audit_at("I5", tmp_path)
    today, later = projected_growth(store.all(), 13, 130)
    assert today == 37
    assert later == 370
