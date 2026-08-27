"""Three stores must be checked, not assumed. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.store.graph import EntityGraph
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

HybridStore = _solution.HybridStore
PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("hy") / "m.jsonl")
    ingest(store, PRIYA, at("I6"))
    return store.all()


@pytest.fixture
def store(memories):
    s = HybridStore()
    s.write(memories)
    return s


def test_stub_is_runnable(memories) -> None:
    s = _lab.HybridStore()
    s.rows.add(memories)
    with pytest.raises(NotImplementedError):
        s.check()


def test_a_fan_out_write_leaves_them_agreeing(store, memories) -> None:
    assert len(store.rows.all()) == len(memories) == 37
    assert len(store.eligible(PRIYA)) == 18
    assert store.check() == []


def test_a_skipped_vector_index_is_caught(memories) -> None:
    s = HybridStore()
    s.rows.add(memories)
    s.graph = EntityGraph().build(memories)
    assert {d.what for d in s.check()} == {"vector", "tombstone"}


def test_an_untombstoned_retirement_is_caught(store) -> None:
    """The failure that hides: rows say retired, the vector still serves it."""
    store.vectors.tombstoned.clear()
    assert [d.what for d in store.check()] == ["tombstone"]


def test_a_stale_graph_is_caught(store) -> None:
    store.graph = EntityGraph()
    assert [d.what for d in store.check()] == ["graph"]


def test_the_graph_cannot_drift_because_it_is_rebuilt(store, memories) -> None:
    """Derived fresh from the source of record, so no invalidation story needed."""
    before = dict(store.graph.shape())
    store.write(memories)
    assert store.graph.shape() == before
    assert store.check() == []


def test_a_divergence_hides_behind_whichever_store_is_asked(store) -> None:
    """The stretch: eligible() still looks right while the vector index lies."""
    store.vectors.tombstoned.clear()
    assert len(store.eligible(PRIYA)) == 18, "SQL validity filter still excludes it"

    retired = [m for m in store.rows.all() if not m.is_live]
    servable = store.vectors.live(store.rows.all())
    assert any(m.id in {r.id for r in retired} for m in servable), (
        "and an audit path would serve a retired belief as current"
    )
