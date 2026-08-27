"""Only semantic memories can contradict. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

can_contradict = _solution.can_contradict
contradiction_candidates = _solution.contradiction_candidates


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("tax") / "m.jsonl")
    ingest(store, Scope(user="priya"))
    return store.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.can_contradict(memories[0])


def test_the_routing_distribution(memories) -> None:
    counts = {t: sum(1 for m in memories if m.type is t) for t in MemoryType}
    assert counts[MemoryType.SEMANTIC] == 22
    assert counts[MemoryType.EPISODIC] == 12
    assert counts[MemoryType.PROCEDURAL] == 2
    assert counts[MemoryType.WORKING] == 0, "nothing durable should be working memory"


def test_only_semantic_can_contradict(memories) -> None:
    """The lesson's central claim, as an assertion."""
    assert all(m.type is MemoryType.SEMANTIC for m in memories if can_contradict(m))
    assert not any(can_contradict(m) for m in memories if m.type is MemoryType.EPISODIC)


def test_the_contradictions_are_already_present(memories) -> None:
    groups = contradiction_candidates(memories)
    assert {"beverage", "response_style", "diet"} <= set(groups)

    beverage = {m.content for m in groups["beverage"]}
    assert "Priya does not drink coffee" in beverage
    assert "Priya drinks three coffees a day" in beverage

    style = {m.content for m in groups["response_style"]}
    assert "Priya prefers detailed explanations with reasoning" in style
    assert "Priya prefers shorter answers" in style


def test_nothing_has_been_retired(memories) -> None:
    """Every side of every contradiction is live. That is the Level 2 backlog."""
    assert all(m.is_live and m.superseded_by is None for m in memories)
