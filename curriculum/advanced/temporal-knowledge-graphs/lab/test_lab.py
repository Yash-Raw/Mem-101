"""Two graphs, one broken edge, and three states that all report zero."""
from __future__ import annotations

from dataclasses import replace as dc_replace
from datetime import UTC, datetime

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.store.graph import EntityGraph
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

cascade = _solution.cascade
edges = _solution.edges
orphans = _solution.orphans
shape = _solution.shape

NOW = datetime(2026, 8, 27, tzinfo=UTC)


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("tk") / "m.jsonl")
    ingest(s, Scope(user="priya"), at("A1"))
    return s.all()


def _naive_orphans(memories):
    by_id = {m.id: m for m in memories}
    return [
        m
        for m in memories
        if m.is_live
        and m.derived_from
        and (srcs := [by_id[r] for r in m.derived_from if r in by_id])
        and all(not s.is_live for s in srcs)
    ]


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.orphans(memories)


def test_the_entity_graph_still_has_no_edges(memories) -> None:
    """A1's parser did not change what graph-stores measured."""
    g = EntityGraph()
    g.build(memories)
    assert g.shape() == {"nodes": 1, "entity_edges": 0, "max_hops": 1}


def test_the_derivation_graph_is_the_one_that_exists(memories) -> None:
    assert shape(memories) == {"derived": 1, "edges": 1, "unresolvable": 0}


def test_a_healthy_derived_fact_looks_exactly_like_an_orphan(memories) -> None:
    """Merge retires the loser and hands its evidence to the winner."""
    derived = next(m for m in memories if m.derived_from)
    source = next(s for s in memories if s.id in derived.derived_from)
    assert derived.is_live and not source.is_live
    assert source.superseded_by == derived.id


def test_the_naive_definition_retires_a_correct_belief(memories) -> None:
    assert len(_naive_orphans(memories)) == 1
    assert "Sam still works nights" in _naive_orphans(memories)[0].content
    assert orphans(memories) == []


def test_the_cascade_moves_nothing_here(memories) -> None:
    live = sum(m.is_live for m in memories)
    assert live == 30
    assert sum(m.is_live for m in cascade(memories, NOW)) == 30


def test_the_naive_cascade_would_take_it_to_29(memories) -> None:
    """One correct belief, deleted by a definition that is four words short."""
    naive = {m.id for m in _naive_orphans(memories)}
    survivors = sum(1 for m in memories if m.is_live and m.id not in naive)
    assert survivors == 29


def test_a_broken_namespace_reports_the_same_zero(memories) -> None:
    """The distinguishing number is `unresolvable`, not the orphan count."""
    derived = next(m for m in memories if m.derived_from)
    source = next(s for s in memories if s.id in derived.derived_from)
    broken = [
        dc_replace(m, derived_from=(source.provenance.source_id,))
        if m.id == derived.id
        else m
        for m in memories
    ]
    assert shape(broken)["unresolvable"] == 1
    assert orphans(broken) == []
    assert shape(memories)["unresolvable"] == 0
    assert orphans(memories) == []


def test_unresolvable_edges_are_reported_not_dropped(memories) -> None:
    derived = next(m for m in memories if m.derived_from)
    broken = [
        dc_replace(m, derived_from=("no-such-memory",)) if m.id == derived.id else m
        for m in memories
    ]
    e = edges(broken)
    assert len(e) == 1, "a shorter list is how the failure stays invisible"
    assert e[0].resolved is False


def test_cascade_runs_to_a_fixed_point(memories) -> None:
    """A summary of a summary needs more than one pass."""
    a, b, *_ = [m for m in memories if m.is_live]
    chain = [
        *memories,
        dc_replace(a, content="derived one", derived_from=(b.id,), id=""),
    ]
    root = next(m for m in chain if m.id == b.id)
    chain = [
        dc_replace(m, invalid_at=NOW, superseded_by="something-else")
        if m.id == root.id
        else m
        for m in chain
    ]
    out = cascade(chain, NOW)
    assert not next(m for m in out if m.content == "derived one").is_live
