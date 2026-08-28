"""Two nullable columns, 37 live records, no id moved."""
from __future__ import annotations

import hashlib

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.temporal.anchor import anchor_all
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

backfill = _solution.backfill
compatibility = _solution.compatibility
strip = _solution.strip

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def stores(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("sm") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    return s.all(), strip(s.all())


def test_stub_is_runnable(stores) -> None:
    current, _before = stores
    with pytest.raises(NotImplementedError):
        _lab.strip(current)


def test_all_four_compatibility_rules_hold(stores) -> None:
    current, before = stores
    after = next(m for m in current if "before the move" in m.content)
    prior = next(m for m in before if m.id == after.id)
    rules = compatibility(prior, after)
    assert len(rules) == 4
    assert all(r.holds for r in rules)


def test_no_id_moved(stores) -> None:
    """The rule that could not be arranged when the migration arrived."""
    current, before = stores
    assert [m.id for m in current] == [m.id for m in before]


def test_the_id_hashes_identity_not_state(stores) -> None:
    current, _before = stores
    m = current[0]
    key = (
        f"{m.scope.user}|{m.type.value}|{m.content}|{m.provenance.source_id}"
    )
    assert hashlib.sha256(key.encode()).hexdigest()[:16] == m.id
    assert "valid_from" not in key


def test_the_backfill_updates_four_of_thirty_seven(stores) -> None:
    _current, before = stores
    _filled, report = backfill(before, anchor_all)
    assert (report.considered, report.updated, report.unchanged) == (37, 4, 33)


def test_it_is_restartable_because_it_is_deterministic(stores) -> None:
    _current, before = stores
    filled, _first = backfill(before, anchor_all)
    _again, second = backfill(filled, anchor_all)
    assert second.updated == 0


def test_the_backfill_reproduces_the_shipped_store(stores) -> None:
    current, before = stores
    filled, _report = backfill(before, anchor_all)
    assert [m.valid_from for m in filled] == [m.valid_from for m in current]


def test_old_records_still_answer_at_lower_precision(stores) -> None:
    """Degradation rather than outage -- which is why the backfill is optional."""
    from memlab.temporal.clocks import event_start

    _current, before = stores
    assert all(m.valid_from is None for m in before)
    assert all(event_start(m) is not None for m in before)


def test_only_the_resolvable_phrases_change(stores) -> None:
    _current, before = stores
    filled, _report = backfill(before, anchor_all)
    changed = [
        after.content
        for prior, after in zip(before, filled, strict=True)
        if prior.valid_from != after.valid_from
    ]
    assert len(changed) == 4
    assert any("before the move" in c for c in changed)
