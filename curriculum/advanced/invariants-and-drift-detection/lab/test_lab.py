"""Seven invariants, two kinds, and one that could not fail."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from memlab import labkit
from memlab.app import chat
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Memory, MemoryType, Provenance, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Kind = _solution.Kind
by_kind = _solution.by_kind
check = _solution.check
failing = _solution.failing

PRIYA = Scope(user="priya")


def _store(tmp_path, profile, rogue=False):
    original = chat._agent_memories
    try:
        if rogue:
            chat._agent_memories = lambda s: [
                *original(s),
                Memory(
                    content="Priya works at Meridian",
                    type=MemoryType.SEMANTIC,
                    scope=Scope(user="priya"),
                    happened_at=datetime(2027, 5, 16, tzinfo=UTC),
                    provenance=Provenance(
                        source_id="t:z", speaker="travel-agent", authority=0.3
                    ),
                    confidence=0.3,
                ),
            ]
            pipeline = at(profile).with_stage(admit=None)
        else:
            pipeline = at(profile)
        store = JsonlStore(tmp_path / f"{profile}-{rogue}.jsonl")
        store.clear()
        ingest(store, PRIYA, pipeline)
        return store.all()
    finally:
        chat._agent_memories = original


def test_stub_is_runnable(tmp_path) -> None:
    with pytest.raises(NotImplementedError):
        _lab.check(_store(tmp_path, "A3"), PRIYA)


def test_all_seven_hold_at_a3(tmp_path) -> None:
    violations = check(_store(tmp_path, "A3"), PRIYA)
    assert len(violations) == 7
    assert failing(violations) == []


def test_five_structural_two_policy(tmp_path) -> None:
    violations = check(_store(tmp_path, "A3"), PRIYA)
    assert len(by_kind(violations, Kind.STRUCTURAL)) == 5
    assert len(by_kind(violations, Kind.POLICY)) == 2


def test_they_catch_a_real_historical_bug(tmp_path) -> None:
    """An invariant nobody has seen fail is one nobody knows works."""
    broken = failing(check(_store(tmp_path, "I8"), PRIYA))
    assert len(broken) == 1
    assert broken[0].invariant == "no belief is retired before it was recorded"
    assert broken[0].kind is Kind.STRUCTURAL
    assert failing(check(_store(tmp_path, "A1"), PRIYA)) == []


def test_the_future_dated_write_is_caught(tmp_path) -> None:
    broken = failing(check(_store(tmp_path, "A3", rogue=True), PRIYA))
    assert len(broken) == 1
    assert broken[0].invariant == "no memory is dated past the store's clock"
    assert broken[0].kind is Kind.POLICY


def test_the_whole_store_version_cannot_catch_it(tmp_path) -> None:
    """The outlier redefines the reference it is measured against."""
    memories = _store(tmp_path, "A3", rogue=True)
    stamps = [m.happened_at for m in memories if m.happened_at]
    whole_store = [s for s in stamps if s > max(stamps) + timedelta(days=1)]
    assert whole_store == []


def test_a_boundary_control_and_an_invariant_are_not_redundant(tmp_path) -> None:
    """A3's policy refuses it; the invariant notices what got in another way."""
    guarded = _store(tmp_path, "A3")
    assert not any("Meridian" in m.content for m in guarded)
    assert failing(check(guarded, PRIYA)) == []


def test_every_violation_reports_a_count(tmp_path) -> None:
    for violation in check(_store(tmp_path, "A3"), PRIYA):
        assert violation.count == 0
        assert violation.holds
