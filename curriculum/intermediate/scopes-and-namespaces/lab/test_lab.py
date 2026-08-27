"""Scope is a correctness boundary. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Memory, MemoryType, Provenance, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Namespace = _solution.Namespace
leak_check = _solution.leak_check
partition = _solution.partition
rank_then_filter = _solution.rank_then_filter
visible = _solution.visible

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("ns") / "m.jsonl")
    ingest(store, PRIYA, at("I2"))
    return store.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.Namespace(user="priya").admits(memories[0])


def test_the_store_has_three_namespaces(memories) -> None:
    keys = partition(memories)
    assert set(keys) == {"priya/*/*", "priya/calendar-agent/*", "priya/travel-agent/*"}
    assert len(keys["priya/*/*"]) == 35


def test_the_user_sees_everything_in_their_own_store(memories) -> None:
    assert len(visible(memories, PRIYA)) == len(memories) == 38


def test_an_agent_namespace_excludes_another_agents_writes(memories) -> None:
    seen = visible(memories, Scope(user="priya", agent="calendar-agent"))
    assert len(seen) == 37
    assert not any("Berlin" in m.content for m in seen)


def test_another_user_sees_nothing(memories) -> None:
    assert visible(memories, Scope(user="sam")) == []


def test_the_leak_set_is_empty_for_every_reader(memories) -> None:
    """The assertion worth running in production. Silent failures need one.

    Note what it does NOT claim: the calendar-agent reader cannot see the
    travel agent's row, and that is not a leak -- it is scoping. Only a
    crossed USER boundary counts.
    """
    for scope in (PRIYA, Scope(user="priya", agent="calendar-agent")):
        assert leak_check(memories, scope) == []


def test_cross_tenant_ranking_would_leak(memories) -> None:
    """Two users, similar facts -- where the wrong order stops being harmless."""
    intruder = Memory(
        content="Priya works at Calico Systems",
        type=MemoryType.SEMANTIC,
        scope=Scope(user="someone-else"),
        provenance=Provenance(source_id="x", speaker="user"),
    )
    mixed = [*memories, intruder]
    assert intruder not in visible(mixed, PRIYA), "the filter holds"
    assert leak_check(mixed, PRIYA) == [], "and the assertion agrees"

    # If `visible` were implemented wrongly, the assertion is what catches it.
    leaked = [m for m in mixed if m.scope.user != PRIYA.user]
    assert leaked == [intruder]


def test_hearsay_is_visible_but_carries_its_authority(memories) -> None:
    """Visibility and belief are different questions."""
    berlin = next(m for m in memories if "Berlin" in m.content)
    assert berlin in visible(memories, PRIYA)
    assert berlin.provenance.authority == 0.3
    assert berlin.scope.agent == "travel-agent"
    assert berlin.provenance.speaker == "travel-agent"
