"""Filter, then rank. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.eval.exam import QUESTION
from memlab.pipeline import at, get
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope, Tier

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

eligible = _solution.eligible
employer_rank = _solution.employer_rank
rank_then_filter = _solution.rank_then_filter

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("sr") / "m.jsonl")
    ingest(store, PRIYA, at("I5"))
    return store.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.eligible(memories, PRIYA)


def test_filtering_shrinks_the_pool(memories) -> None:
    live = [m for m in memories if m.is_live]
    assert (len(live), len(eligible(memories, PRIYA))) == (30, 18)


def test_and_lifts_the_answer_eight_places(memories) -> None:
    """No ranking changed. The candidate set did."""
    live = [m for m in memories if m.is_live]
    assert employer_rank(QUESTION, live) == 20
    assert employer_rank(QUESTION, eligible(memories, PRIYA)) == 12


def test_the_demoted_filler_is_gone(memories) -> None:
    kept = {m.content for m in eligible(memories, PRIYA)}
    assert "Priya mostly does pipeline work" not in kept


def test_everything_returned_is_live_and_long_term(memories) -> None:
    assert all(
        m.is_live and m.tier is Tier.LONG_TERM for m in eligible(memories, PRIYA)
    )


def test_rank_then_filter_returns_fewer_than_k(memories) -> None:
    assert len(rank_then_filter(QUESTION, memories, PRIYA, k=5)) < 5


def test_a_stranger_sees_nothing(memories) -> None:
    assert eligible(memories, Scope(user="someone-else")) == []


def test_the_guard_fails_open_on_an_untiered_store(tmp_path) -> None:
    """Beginner never assigned tiers. Failing closed would return nothing."""
    store = JsonlStore(tmp_path / "b.jsonl")
    ingest(store, PRIYA, get("beginner"))
    assert len(eligible(store.all(), PRIYA)) == 36
