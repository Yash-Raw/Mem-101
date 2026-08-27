"""There is no good k. Asserted."""
from __future__ import annotations

from datetime import UTC

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

sweep_k = _solution.sweep_k

PRIYA = Scope(user="priya")
KS = [3, 5, 10, 15, 20, 25, 30, 36]


@pytest.fixture(scope="module")
def rows(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("sweep") / "m.jsonl")
    ingest(store, PRIYA)
    return sweep_k(store.all(), PRIYA, KS)


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.contradictions_in_context("anything")


def test_low_k_recalls_no_employer_at_all(rows) -> None:
    assert {k: e for k, e, _, _ in rows}[5] == "-"


def test_medium_k_is_confidently_wrong(rows) -> None:
    """The worst cell in the table: a real fact, and it is the dead one."""
    assert {k: e for k, e, _, _ in rows}[10] == "Northwind only"


def test_high_k_is_ambiguous_rather_than_correct(rows) -> None:
    states = {k: e for k, e, _, _ in rows}
    assert states[20] == "both, ambiguous"
    assert states[36] == "both, ambiguous"


def test_no_k_is_ever_correct_and_unambiguous(rows) -> None:
    """The lesson, as a single assertion."""
    assert not any(state == "Calico only" for _, state, _, _ in rows)


def test_contradictions_only_ever_increase(rows) -> None:
    counts = [c for _, _, _, c in rows]
    assert counts == sorted(counts), "raising k never removes a contradiction"
    assert counts[0] == 0 and counts[-1] == 3


def test_validity_filtering_would_fix_every_row_at_once(tmp_path) -> None:
    """Retire the stale employer and re-sweep. One field changes everything."""
    from datetime import datetime

    store = JsonlStore(tmp_path / "m.jsonl")
    ingest(store, PRIYA)
    memories = [
        m.supersede(by="x", at=datetime(2026, 1, 1, tzinfo=UTC))
        if "Northwind" in m.content else m
        for m in store.all()
    ]
    live = [m for m in memories if m.is_live]
    states = {k: e for k, e, _, _ in sweep_k(live, PRIYA, KS)}
    assert "Northwind only" not in states.values()
    assert "both, ambiguous" not in states.values()
