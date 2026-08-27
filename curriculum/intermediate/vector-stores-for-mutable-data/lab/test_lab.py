"""A cached vector cannot see supersession. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.eval.exam import QUESTION
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

VectorIndex = _solution.VectorIndex
PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("vec") / "m.jsonl")
    ingest(store, PRIYA, at("I6"))
    return store.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.VectorIndex().index(memories)


def test_one_vector_per_memory(memories) -> None:
    index = VectorIndex()
    assert index.index(memories) == len(memories) == 37


def test_indexing_is_idempotent(memories) -> None:
    """Content-addressed ids mean a second pass computes nothing."""
    index = VectorIndex()
    index.index(memories)
    assert index.index(memories) == 0


def test_queries_are_served_from_cache(memories) -> None:
    index = VectorIndex()
    index.index(memories)
    for _ in range(3):
        index.search(QUESTION, memories, k=5)
    assert index.stats == {
        "vectors": 37, "tombstoned": 7, "computed": 40, "served_from_cache": 90
    }


def test_the_uncached_cost_is_2n_per_query(memories) -> None:
    assert 3 * 2 * len(memories) == 222


def test_retired_beliefs_are_tombstoned_not_dropped(memories) -> None:
    """The vector stays -- audit needs it. Default retrieval must not see it."""
    index = VectorIndex()
    index.index(memories)
    retired = [m for m in memories if not m.is_live]
    assert len(retired) == 7
    for m in retired:
        assert m.id in index.vectors, "the vector survives"
        assert m.id in index.tombstoned, "and is not served"
    assert len(index.live(memories)) == 30


def test_the_cache_cannot_detect_supersession_itself(memories) -> None:
    """Content unchanged, id unchanged, vector correct. Only invalid_at moved."""
    from memlab.llm.fake import embed_text

    retired = next(m for m in memories if not m.is_live and "Northwind" in m.content)
    index = VectorIndex()
    index.index(memories)
    assert index.vectors[retired.id] == embed_text(retired.content), (
        "the cached vector is a perfectly correct embedding of live text"
    )


def test_search_excludes_tombstoned_memories(memories) -> None:
    index = VectorIndex()
    index.index(memories)
    hits = index.search(QUESTION, memories, k=len(memories))
    assert not any("data engineer at Northwind" in m.content for _s, m in hits)


def test_the_uncached_curve_is_2n(memories) -> None:
    """Illustrative scale, verified rather than quoted."""
    curve = _solution.replication_curve(memories)
    assert curve == [(37, 74), (740, 1480), (1850, 3700)]
    for size, calls in curve:
        assert calls == 2 * size


def test_the_wired_pipeline_makes_two_calls_per_query(tmp_path) -> None:
    """One per sub-question, after query-formulation splits the compound."""
    import memlab.retrieve.hybrid as H
    from memlab.app.chat import ask

    pipeline = at("I7")
    store = JsonlStore(tmp_path / "m.jsonl")
    ingest(store, PRIYA, pipeline)
    pipeline.vectors.index(store.all())

    calls = [0]
    original = H.embed_text
    H.embed_text = lambda t, _o=original: (calls.__setitem__(0, calls[0] + 1), _o(t))[1]
    try:
        ask(store, PRIYA, QUESTION, k=5, pipeline=pipeline)
    finally:
        H.embed_text = original
    assert calls[0] == 2
