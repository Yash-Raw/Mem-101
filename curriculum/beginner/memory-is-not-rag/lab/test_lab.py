"""The failure this lab exists to demonstrate, asserted.

These tests do not check that retrieval works. They check that *working*
retrieval still cannot answer the question. That gap is the course.
"""
from __future__ import annotations

import itertools

import pytest
from memlab import labkit
from memlab.fixtures import load_turns

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

QUESTION = _solution.QUESTION
history = _solution.history
retrieve_topk = _solution.retrieve_topk


def ranked() -> list[tuple[float, dict]]:
    turns = history()
    return retrieve_topk(QUESTION, turns, k=len(turns))


def rank_of(hits, needle: str) -> int | None:
    for i, (_, t) in enumerate(hits, 1):
        if needle in t["text"]:
            return i
    return None


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.retrieve_topk("anything", _lab.history())


def test_the_retriever_is_not_broken() -> None:
    """Establish this first, so the failure cannot be blamed on bad retrieval."""
    hits = ranked()
    assert all(a[0] >= b[0] for a, b in itertools.pairwise(hits)), "sorted by score"
    # Every relevant fact IS in the index and IS reachable.
    for needle in ("Northwind Labs", "Calico Systems", "vegetarian", "fish", "gluten"):
        assert rank_of(hits, needle) is not None, f"{needle} should be retrievable at all"


def test_the_query_is_not_a_memory() -> None:
    """Session 14 is the question. Leave it in the index and it retrieves itself."""
    assert all(t["session"] < 14 for t in history())
    polluted = [t for t in load_turns() if t["role"] == "user"]
    top = retrieve_topk(QUESTION, polluted, k=1)[0]
    assert top[1]["session"] == 14 and top[0] > 0.6, (
        "with the query left in, the best-scoring 'memory' is the query itself"
    )


def test_the_stale_employer_beats_the_current_one_by_a_mile() -> None:
    """The headline failure. These ranks are quoted in index.md."""
    hits = ranked()
    stale, current = rank_of(hits, "Northwind Labs"), rank_of(hits, "Calico Systems")
    assert stale == 1, f"stale employer should rank 1, got {stale}"
    assert current is not None and current >= 15, (
        f"current employer should be buried near the bottom of {len(hits)}, got {current}. "
        "If this moves, update the ranking table quoted in index.md."
    )
    assert current - stale >= 15, "the gap is the point"


def test_normalising_the_event_helps_but_does_not_save_you() -> None:
    """Isolate the cause, then show it is only half the cause.

    Session 8 phrases the change as an EVENT ("I'm leaving... Starting at").
    The question asks for a STATE. A write path would normalise the event into
    `employer = Calico Systems`, which lifts it from last place to mid-pack --
    genuinely better, and still behind the stale fact from session 1.

    Extraction alone is not enough. Something has to record that one fact
    RETIRED the other, and that mechanism does not exist anywhere in retrieval.
    """
    turns = history()
    before = rank_of(retrieve_topk(QUESTION, turns, k=len(turns)), "Calico Systems")

    normalised = turns + [{
        "session": 8, "ts": "2025-12-08T09:00:00Z", "role": "user",
        "text": "Priya works at Calico Systems as a staff engineer.",
    }]
    hits = retrieve_topk(QUESTION, normalised, k=len(normalised))
    after = rank_of(hits, "works at Calico Systems")

    assert after < before, "normalising the event improves retrievability"
    assert after > rank_of(hits, "Northwind Labs"), (
        "and the stale fact STILL wins — recency and supersession are missing"
    )


def test_nothing_records_that_one_fact_retired_another() -> None:
    """Sessions 1, 7 and 12 form a diet chain. Retrieval returns three peers."""
    hits = ranked()
    retrieved = [t for _, t in hits]
    assert {1, 7, 12} <= {t["session"] for t in retrieved}
    assert all("superseded_by" not in t and "invalid_at" not in t for t in retrieved), (
        "raw turns carry no relationship to one another; a memory record would"
    )
