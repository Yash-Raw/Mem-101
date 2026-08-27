"""The type gates everything downstream. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

can_contradict = _solution.can_contradict
comparisons_avoided = _solution.comparisons_avoided
partition_by_conflict_risk = _solution.partition_by_conflict_risk

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("typed") / "m.jsonl")
    ingest(store, PRIYA)
    return store.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.can_contradict(memories[0])


def test_the_partition(memories) -> None:
    at_risk, safe = partition_by_conflict_risk(memories)
    assert len(at_risk) == 24        # 22 semantic + 2 procedural
    assert len(safe) == 12           # all episodic
    assert len(at_risk) + len(safe) == len(memories) == 36


def test_episodic_is_the_only_structurally_safe_type(memories) -> None:
    """Semantic AND procedural can be contradicted -- procedural is replaced
    wholesale rather than retired per-fact, but it is still at risk."""
    at_risk, safe = partition_by_conflict_risk(memories)
    assert {m.type for m in at_risk} == {MemoryType.SEMANTIC, MemoryType.PROCEDURAL}
    assert {m.type for m in safe} == {MemoryType.EPISODIC}


def test_the_northwind_episodes_are_structurally_safe(memories) -> None:
    """Both permanently true. Retiring either would be data loss."""
    episodes = [
        m for m in memories
        if m.type is MemoryType.EPISODIC and "Northwind" in m.content
    ]
    assert len(episodes) >= 2
    assert not any(can_contradict(m) for m in episodes)


def test_the_coffee_facts_are_at_risk(memories) -> None:
    coffee = [m for m in memories if "coffee" in m.content]
    assert len(coffee) == 2
    assert all(can_contradict(m) for m in coffee)


def test_a_retired_memory_cannot_contradict(memories) -> None:
    from datetime import UTC, datetime

    semantic = next(m for m in memories if m.type is MemoryType.SEMANTIC)
    assert can_contradict(semantic)
    assert not can_contradict(semantic.supersede(by="x", at=datetime.now(UTC)))


def test_typing_shrinks_the_comparison_space(memories) -> None:
    naive, real = comparisons_avoided(memories)
    assert naive == 630 and real == 276
