"""The graph's shape is the measurement. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.entity.aliases import NOT_PEOPLE
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

EntityGraph = _solution.EntityGraph
PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("gr") / "m.jsonl")
    ingest(store, PRIYA, at("I6"))
    return store.all()


@pytest.fixture
def graph(memories):
    return EntityGraph().build(memories)


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.EntityGraph().build(memories).shape()


def test_the_corpus_supports_one_hop(graph) -> None:
    """The finding this lesson is built on."""
    assert graph.shape() == {"nodes": 1, "entity_edges": 0, "max_hops": 1}
    assert graph.nodes == {"samira"}


def test_the_one_node_gathers_four_surface_forms(graph) -> None:
    every = graph.about("samira", live_only=False)
    assert len(every) == 6
    text = " ".join(m.content for m in every)
    for form in ("Sam ", "Samira", "Sammy", "She works"):
        assert form in text


def test_live_only_is_the_default(graph) -> None:
    assert len(graph.about("samira")) == 4
    assert len(graph.about("samira", live_only=False)) == 6


def test_there_is_nothing_to_traverse(graph) -> None:
    assert graph.edges == set()
    assert graph.neighbours("samira") == set()


def test_the_missing_edge_is_upstream(memories) -> None:
    """Sam's employer is in the store and cannot be a node.

    `Aubyn` is on the NOT_PEOPLE stop list -- correctly, it is a hospital -- so
    "where does Priya's partner work?" has no path even though the fact exists.
    The graph's shape is downstream of an extraction decision from I2.
    """
    assert "Aubyn" in NOT_PEOPLE
    employer_fact = next(m for m in memories if "St. Aubyn's" in m.content)
    assert employer_fact.entities == ("samira",), "one entity, so no edge"


def test_an_empty_store_has_no_shape() -> None:
    assert EntityGraph().build([]).shape() == {
        "nodes": 0, "entity_edges": 0, "max_hops": 0
    }


def test_co_mention_would_create_an_edge(memories) -> None:
    """The schema can express an edge -- the corpus just never produces one."""
    from dataclasses import replace

    two = replace(memories[0], entities=("samira", "someone-else"), id="x")
    graph = EntityGraph().build([two])
    assert graph.shape()["entity_edges"] == 1
    assert graph.neighbours("samira") == {"someone-else"}
