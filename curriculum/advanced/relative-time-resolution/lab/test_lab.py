"""Four classes of relative reference, and the one you must not resolve."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import _resolve_dedupe_reconcile_bitemporal, at
from memlab.store.jsonl import JsonlStore
from memlab.temporal.clocks import audit, event_start, turn_timestamps
from memlab.temporal.validity import as_of
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Anchor = _solution.Anchor
classify = _solution.classify
resolve = _solution.resolve

PRIYA = Scope(user="priya")
GOLD = {
    "before the move": datetime(2025, 8, 2, tzinfo=UTC),
    "left Northwind Labs last month": datetime(2025, 12, 1, tzinfo=UTC),
    "gluten intolerance last week": datetime(2026, 5, 8, tzinfo=UTC),
    "since March 2026": datetime(2026, 3, 1, tzinfo=UTC),
}
BEFORE = at("A1").with_stage(
    anchor=None, consolidate=_resolve_dedupe_reconcile_bitemporal
)


def _build(tmp_path_factory, pipeline, tag):
    s = JsonlStore(tmp_path_factory.mktemp(tag) / "m.jsonl")
    ingest(s, PRIYA, pipeline)
    return s.all()


@pytest.fixture(scope="module")
def before(tmp_path_factory):
    return _build(tmp_path_factory, BEFORE, "rtb")


@pytest.fixture(scope="module")
def after(tmp_path_factory):
    return _build(tmp_path_factory, at("A1"), "rta")


def test_stub_is_runnable(before) -> None:
    with pytest.raises(NotImplementedError):
        _lab.classify(before[0])


@pytest.mark.parametrize(
    "fragment,expected",
    [
        ("weekly report process", Anchor.LITERAL),
        ("left Northwind Labs last month", Anchor.OFFSET),
        ("gluten intolerance last week", Anchor.OFFSET),
        ("since March 2026", Anchor.INTERVAL),
        ("before the move", Anchor.EVENT),
        ("Sam still works nights", Anchor.NONE),
    ],
)
def test_classification(before, fragment, expected) -> None:
    m = next(x for x in before if fragment in x.content)
    assert classify(m).anchor is expected


@pytest.mark.parametrize("fragment,truth", list(GOLD.items()))
def test_every_resolvable_phrase_lands_on_gold(after, fragment, truth) -> None:
    m = next(x for x in after if fragment in x.content)
    assert (event_start(m) - truth).days == 0


def test_the_procedure_step_is_left_alone(after) -> None:
    """"diff against last week" is the recipe, not a claim about when."""
    m = next(x for x in after if "weekly report" in x.content)
    assert m.type is MemoryType.PROCEDURAL
    assert m.valid_from is None
    assert classify(m).anchor is Anchor.LITERAL


def test_what_the_guard_prevents(after) -> None:
    """Without it the recipe is dated 2025-09-07 and looks well-formed."""
    m = next(x for x in after if "weekly report" in x.content)
    _phrase, delta = _solution._first_offset(m.content)
    assert str((m.happened_at - delta).date()) == "2025-09-07"


def test_last_month_is_a_calendar_unit_not_thirty_days(after) -> None:
    """As a timedelta it lands on 2025-12-20 -- nineteen days out."""
    m = next(x for x in after if "left Northwind Labs last month" in x.content)
    assert str(event_start(m).date()) == "2025-12-01"
    naive = m.happened_at - timedelta(days=30)
    assert (naive - datetime(2025, 12, 1, tzinfo=UTC)).days == 19


def test_an_unknown_event_declines_rather_than_guesses(after) -> None:
    """A parser that always produces a date is a parser that invents them."""
    from dataclasses import replace as dc_replace

    m = next(x for x in after if "before the move" in x.content)
    unknown = dc_replace(
        m, content="Priya used to cycle before the wedding", valid_from=None
    )
    assert classify(unknown).anchor is Anchor.EVENT
    assert resolve(unknown, after).valid_from is None


def _sweep(memories):
    differ, total, day = 0, 0, datetime(2025, 3, 1, tzinfo=UTC)
    while day < datetime(2026, 9, 1, tzinfo=UTC):
        total += 1
        if {m.id for m in as_of(memories, day)} != {
            m.id for m in as_of(memories, day, believed_at_time=day)
        }:
            differ += 1
        day += timedelta(days=1)
    return differ, total


def test_the_model_stops_being_degenerate(before, after) -> None:
    """0 of 549 -> 257 of 549. Four dates, 47% of the corpus."""
    assert _sweep(before) == (0, 549)
    assert _sweep(after) == (257, 549)


def test_the_audit_undercounts_in_the_safe_direction(after) -> None:
    """4 anchored, 3 reported -- "before the move" lands on a write instant."""
    ts = turn_timestamps()
    anchored = [m for m in after if m.valid_from]
    assert len(anchored) == 4
    assert audit(after, ts).genuinely_distinct == 3
    missed = [m for m in anchored if event_start(m).isoformat()[:19] in ts]
    assert len(missed) == 1
    assert "before the move" in missed[0].content


def test_gold_is_the_answer_key_not_the_lesson(after) -> None:
    """Every date this lab asserts is in gold.yml, including the null one."""
    from memlab.fixtures import load_gold

    entries = {e["phrase"]: e["resolves_to"] for e in load_gold()["relative_time"]}
    assert entries["last month"] == date(2025, 12, 1)
    assert entries["since March 2026"] == date(2026, 3, 1)
    assert entries["Before the move"] == date(2025, 8, 2)
    assert entries["last week"] == date(2026, 5, 8)
    assert entries["diff against last week"] is None, "the one that must not resolve"


def test_a_memory_with_no_phrase_keeps_the_ingestion_time(after) -> None:
    """gold: the promotion date must be inferred from ingestion time alone."""
    m = next(x for x in after if "promotion to charge nurse" in x.content)
    assert m.valid_from is None
    assert str(event_start(m).date()) == "2025-04-22"


def test_happened_at_never_moves(before, after) -> None:
    """A dozen Level 1 and 2 figures are measured against it."""
    was = {m.id: m.happened_at for m in before}
    for m in after:
        if m.id in was:
            assert m.happened_at == was[m.id]
