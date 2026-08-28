"""Price each topology by what a reader loses -- and by what leaks."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Topology = _solution.Topology
readable = _solution.readable
shape = _solution.shape

PRIYA = Scope(user="priya")
CALENDAR = Scope(user="priya", agent="calendar-agent")
TRAVEL = Scope(user="priya", agent="travel-agent")
PII = ("47 Halloway Road", "07700 900412")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("mt") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    return s.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.shape(memories)


def test_the_shape_nobody_chose(memories) -> None:
    found = shape(memories)
    assert found.topology == Topology.HIERARCHICAL
    assert found.namespaces == {
        "priya/*/*": 34,
        "priya/calendar-agent/*": 2,
        "priya/travel-agent/*": 1,
    }


@pytest.mark.parametrize(
    "reader,private,hierarchical,shared",
    [
        (PRIYA, 34, 37, 37),
        (CALENDAR, 2, 36, 37),
        (TRAVEL, 1, 35, 37),
    ],
    ids=["user", "calendar-agent", "travel-agent"],
)
def test_what_each_reader_loses(memories, reader, private, hierarchical, shared) -> None:
    assert len(readable(memories, reader, Topology.PRIVATE)) == private
    assert len(readable(memories, reader, Topology.HIERARCHICAL)) == hierarchical
    assert len(readable(memories, reader, Topology.SHARED)) == shared


def test_for_the_user_hierarchical_and_shared_are_identical(memories) -> None:
    """Whatever the current shape isolates, it is not the user from an agent."""
    a = {m.id for m in readable(memories, PRIYA, Topology.HIERARCHICAL)}
    b = {m.id for m in readable(memories, PRIYA, Topology.SHARED)}
    assert a == b


def test_private_leaves_an_agent_with_only_its_own_write(memories) -> None:
    seen = readable(memories, TRAVEL, Topology.PRIVATE)
    assert len(seen) == 1
    assert seen[0].provenance.speaker == "travel-agent"


def test_hierarchical_leaks_exactly_what_shared_leaks(memories) -> None:
    """The shape chosen for us is not a privacy boundary."""
    def leaked(topology):
        return sorted(
            m.content
            for m in readable(memories, TRAVEL, topology)
            if any(k in m.content for k in PII)
        )

    assert len(leaked(Topology.PRIVATE)) == 0
    assert len(leaked(Topology.HIERARCHICAL)) == 2
    assert leaked(Topology.HIERARCHICAL) == leaked(Topology.SHARED)
    assert any("47 Halloway Road" in c for c in leaked(Topology.SHARED))


def test_the_user_loses_three_under_private(memories) -> None:
    """The stretch: the agent-written memories, two of them load-bearing."""
    full = {m.id for m in readable(memories, PRIYA, Topology.HIERARCHICAL)}
    private = {m.id for m in readable(memories, PRIYA, Topology.PRIVATE)}
    lost = [m for m in memories if m.id in full - private]
    assert len(lost) == 3
    assert all(m.scope.agent for m in lost)


def test_topology_is_str_backed_so_equality_survives_module_copies() -> None:
    """A lab and its solution import different enum classes; `is` fails."""
    assert Topology.SHARED == "shared"
    assert _lab.Topology.SHARED == Topology.SHARED
    assert _lab.Topology.SHARED is not Topology.SHARED
