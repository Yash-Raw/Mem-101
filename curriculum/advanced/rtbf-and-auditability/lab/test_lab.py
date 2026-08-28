"""Proof that holds none of what it proves."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.privacy.classify import Kind
from memlab.privacy.delete import Request, cascade, purge, resolve
from memlab.store.jsonl import JsonlStore
from memlab.store.sqlite import SqliteStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

RETENTION = _solution.RETENTION
issue = _solution.issue
rescan = _solution.rescan

PRIYA = Scope(user="priya")
NOW = datetime(2026, 6, 20, tzinfo=UTC)


@pytest.fixture
def deleted(tmp_path):
    pipeline = at("A3")
    store = JsonlStore(tmp_path / "m.jsonl")
    store.clear()
    ingest(store, PRIYA, pipeline)
    memories = store.all()
    pipeline.vectors.index(memories)
    sqlite = SqliteStore(tmp_path / "m.db")
    sqlite.clear()
    sqlite.add(memories)

    request = Request(text="forget my old address", session=13, at=NOW)
    target = resolve(request, memories, Kind.ADDRESS).candidates[0]
    result = cascade(target, memories, pipeline.vectors, sqlite)
    kept = purge(target, memories)
    residue = rescan(kept, target.id, extra=[sqlite.all()])
    receipt = issue(
        target, Kind.ADDRESS.value, request.session, request.at, NOW,
        {
            "primary": result.primary, "sqlite": result.sqlite,
            "vectors": result.vectors, "derived": result.derived,
            "summaries": result.summaries,
        },
        residue,
    )
    return target, kept, receipt


def test_stub_is_runnable(tmp_path) -> None:
    with pytest.raises(NotImplementedError):
        _lab.rescan([], "abc")


def test_the_receipt_holds_none_of_the_content(deleted) -> None:
    _target, _kept, receipt = deleted
    assert "Halloway" not in str(receipt)
    assert "Bristol" not in str(receipt)
    assert "forget my old address" not in str(receipt), "not even the request"


def test_the_id_proves_it_to_whoever_holds_the_original(deleted) -> None:
    target, kept, receipt = deleted
    assert receipt.proves(target)
    assert not receipt.proves(next(m for m in kept if m.id != target.id))
    assert len(receipt.memory_id) == 16


def test_the_rescan_comes_back_empty(deleted) -> None:
    _target, _kept, receipt = deleted
    assert receipt.residue == 0
    assert receipt.complete


def test_completeness_is_about_what_remains_not_what_was_done(deleted) -> None:
    """A cascade that misses a fourth copy reports success on its own terms."""
    target, kept, receipt = deleted
    survivor = [*kept, target]
    assert rescan(survivor, target.id) == 1
    assert receipt.structures["primary"] == 1, "the cascade still claims it removed one"


def test_the_zeroes_are_kept(deleted) -> None:
    _t, _k, receipt = deleted
    assert receipt.structures["derived"] == 0
    assert receipt.structures["summaries"] == 0
    assert receipt.reached == ("primary", "sqlite", "vectors")


def test_the_rescan_takes_an_id_not_content(deleted) -> None:
    """Searching by content means holding the content."""
    target, kept, _r = deleted
    assert rescan(kept, target.id) == 0
    assert rescan([target], target.id) == 1


def test_receipts_expire(deleted) -> None:
    """A permanent record that someone asked to be forgotten."""
    _t, _k, receipt = deleted
    assert not receipt.expired(NOW + timedelta(days=100))
    assert receipt.expired(NOW + timedelta(days=366))
    assert RETENTION == timedelta(days=365)


def test_the_fingerprint_property_predates_this_module(deleted) -> None:
    """Content-addressed since Beginner, for deduplication."""
    target, _k, receipt = deleted
    import hashlib

    assert target.id == target._derive_id()
    assert receipt.memory_id == target.id
    key = (
        f"{target.scope.user}|{target.type.value}|{target.content}"
        f"|{target.provenance.source_id}"
    )
    assert hashlib.sha256(key.encode()).hexdigest()[:16] == target.id
