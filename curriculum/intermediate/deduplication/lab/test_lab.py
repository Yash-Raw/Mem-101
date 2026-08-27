"""Idempotency did not catch this. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

_eligible = _solution._eligible
dedupe = _solution.dedupe
duplicate_pairs = _solution.duplicate_pairs
near_miss_scores = _solution.near_miss_scores

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    """As I2 left the store: resolved, not yet deduplicated."""
    store = JsonlStore(tmp_path_factory.mktemp("dd") / "m.jsonl")
    ingest(store, PRIYA, at("I2"))
    return store.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab._eligible(memories[0], memories[1])


def test_idempotency_did_not_prevent_this(memories) -> None:
    """Same content, different source, different id -- invisible to write-time dedup."""
    calico = [m for m in memories if m.content == "Priya works at Calico Systems"]
    assert len(calico) == 2
    assert calico[0].id != calico[1].id
    assert {m.provenance.source_id.split(":")[0] for m in calico} == {"s8", "s9"}


def test_exactly_one_merge_at_certainty(memories) -> None:
    merges = duplicate_pairs(memories)
    assert len(merges) == 1
    assert merges[0].similarity == pytest.approx(1.0)
    assert merges[0].kept.provenance.source_id.startswith("s8"), "keep the earlier one"


def test_the_store_shrinks_by_one(memories) -> None:
    after = dedupe(memories)
    assert (len(memories), len(after)) == (38, 37)


def test_the_survivor_is_corroborated(memories) -> None:
    after = dedupe(memories)
    kept = next(m for m in after if m.content == "Priya works at Calico Systems")
    assert kept.confidence > 1.0 - 1e-9 or kept.confidence >= 1.0


def test_every_near_miss_survives(memories) -> None:
    """The three pairs a lower threshold would wrongly collapse."""
    after = dedupe(memories)
    scores = near_miss_scores(after)
    assert len(scores) == 3
    assert all(0.6 < s < 0.8 for s, _, _ in scores)


def test_type_gate_protects_event_and_state(memories) -> None:
    """0.739 apart, and merging them would lose a date or a standing fact."""
    event = next(m for m in memories if "was diagnosed with a gluten" in m.content)
    state = next(m for m in memories if m.content == "Priya has a gluten intolerance")
    assert event.type is MemoryType.EPISODIC and state.type is MemoryType.SEMANTIC
    assert not _eligible(event, state)


def test_dedupe_is_idempotent(memories) -> None:
    once = dedupe(memories)
    assert [m.id for m in dedupe(once)] == [m.id for m in once]
