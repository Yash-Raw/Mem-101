"""Idempotency, and what a duplicate costs. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.extract.naive import extract
from memlab.fixtures import load_turns
from memlab.retrieve.embedding import EmbeddingRetriever
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

IdempotentStore = _solution.IdempotentStore
NaiveStore = _solution.NaiveStore

SCOPE = Scope(user="priya")


def ingest_all(store) -> int:
    return sum(
        store.add(extract(t, SCOPE))
        for t in load_turns(user_only=True)
        if t["session"] < 14
    )


def test_stub_is_runnable(tmp_path) -> None:
    with pytest.raises(NotImplementedError):
        _lab.IdempotentStore(tmp_path / "x.jsonl").add([])


def test_second_ingest_is_a_no_op(tmp_path) -> None:
    store = IdempotentStore(tmp_path / "m.jsonl")
    assert ingest_all(store) == 36
    assert ingest_all(store) == 0
    assert len(store.all()) == 36


def test_the_naive_store_doubles(tmp_path) -> None:
    store = NaiveStore(tmp_path / "m.jsonl")
    ingest_all(store)
    ingest_all(store)
    assert len(store.all()) == 72


def test_a_duplicate_evicts_a_different_fact(tmp_path) -> None:
    """The real cost: top-k is a fixed budget, and a duplicate spends two slots."""
    clean, dirty = IdempotentStore(tmp_path / "c.jsonl"), NaiveStore(tmp_path / "d.jsonl")
    ingest_all(clean)
    ingest_all(dirty)
    ingest_all(dirty)

    r = EmbeddingRetriever()
    clean_hits = r.search("where do I work?", clean.all(), SCOPE, k=5)
    dirty_hits = r.search("where do I work?", dirty.all(), SCOPE, k=5)

    assert len({h.memory.content for h in clean_hits}) == 5
    assert len({h.memory.content for h in dirty_hits}) < 5, (
        "duplicates consume slots that distinct memories would have filled"
    )


def test_roundtrip_survives_a_new_store_object(tmp_path) -> None:
    path = tmp_path / "m.jsonl"
    ingest_all(IdempotentStore(path))
    assert len(IdempotentStore(path).all()) == 36


def test_live_and_all_agree_while_nothing_is_retired(tmp_path) -> None:
    """The seam exists; Level 2 gives it something to do."""
    store = IdempotentStore(tmp_path / "m.jsonl")
    ingest_all(store)
    assert len(store.live()) == len(store.all())
