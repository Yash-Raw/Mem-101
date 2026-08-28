"""Two axes, two predicates, and a corpus on which they never disagree."""
from __future__ import annotations

from dataclasses import replace as dc_replace
from datetime import UTC, datetime, timedelta

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import _resolve_dedupe_reconcile_bitemporal, at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

as_of = _solution.as_of
believed_at = _solution.believed_at
held_at = _solution.held_at

PRIYA = Scope(user="priya")
JUNE_2025 = datetime(2025, 6, 1, tzinfo=UTC)
NOW = datetime(2026, 8, 27, tzinfo=UTC)
EMPLOYER = ("Northwind", "Calico")

# A1 as this lesson leaves it: the two axes separated, and nothing yet reading
# an event date off the language. `relative-time-resolution` lands the parser
# and moves these numbers on purpose, so the measurement is pinned explicitly
# rather than to `at("A1")`.
BEFORE_THE_PARSER = at("A1").with_stage(
    anchor=None, consolidate=_resolve_dedupe_reconcile_bitemporal
)



def _build(tmp_path_factory, module):
    s = JsonlStore(tmp_path_factory.mktemp(f"vi{module.name}") / "m.jsonl")
    ingest(s, PRIYA, module)
    return s.all()


@pytest.fixture(scope="module")
def i8(tmp_path_factory):
    return _build(tmp_path_factory, at("I8"))


@pytest.fixture(scope="module")
def a1(tmp_path_factory):
    return _build(tmp_path_factory, BEFORE_THE_PARSER)


def _employer(ms):
    return [m for m in ms if any(e in m.content for e in EMPLOYER)]


def test_stub_is_runnable(a1) -> None:
    with pytest.raises(NotImplementedError):
        _lab.as_of(a1, JUNE_2025)


def test_the_june_question_has_exactly_one_answer(a1) -> None:
    answer = _employer(as_of(a1, JUNE_2025))
    assert len(answer) == 1
    assert "data engineer at Northwind Labs" in answer[0].content


def test_the_level_two_read_path_answers_with_the_future(a1) -> None:
    """Four facts about a job she had not been offered yet."""
    live = _employer([m for m in a1 if m.is_live])
    assert len(live) == 4
    assert not any(held_at(m, JUNE_2025) for m in live), (
        "not one of them was true on the date asked about"
    )
    assert all(m.happened_at > JUNE_2025 for m in live)


def test_the_memory_that_answers_it_carries_both_instants(a1) -> None:
    """True from 2025-03-04, retired 2025-12-08. Sufficient all along."""
    m = next(x for x in a1 if "data engineer at Northwind" in x.content)
    assert str(m.happened_at.date()) == "2025-03-04"
    assert str(m.invalid_at.date()) == "2025-12-08"
    assert m.happened_at < JUNE_2025 < m.invalid_at


def test_the_split_closes_seven_intervals(i8, a1) -> None:
    assert sum(1 for m in i8 if m.valid_to) == 0
    assert sum(1 for m in a1 if m.valid_to) == 7


def test_a_belief_no_longer_ends_before_it_begins(i8, a1) -> None:
    """The Berlin claim: recorded 2026-05-16, retired 2025-08-02."""
    bad_i8 = [m for m in i8 if m.invalid_at and m.invalid_at < m.recorded_at]
    assert len(bad_i8) == 1
    assert "Berlin" in bad_i8[0].content
    assert [m for m in a1 if m.invalid_at and m.invalid_at < m.recorded_at] == []


def test_the_split_fixes_the_present_not_the_past(i8, a1) -> None:
    """Both answer June 2025. Only @A1 answers "now"."""
    assert len(_employer(as_of(i8, JUNE_2025))) == 1
    assert len(_employer(as_of(a1, JUNE_2025))) == 1
    assert len(_employer(as_of(i8, NOW))) == 5
    assert len(_employer(as_of(a1, NOW))) == 4


def test_the_belief_clock_is_no_longer_the_wall_clock(a1) -> None:
    """One instant for a seventeen-month conversation answered nothing."""
    assert len({m.recorded_at.date() for m in a1}) == 15


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


def test_the_two_axes_never_disagree(a1) -> None:
    """0 of 549. Both populated, both correct, and the model is degenerate."""
    assert _sweep(a1) == (0, 549)


def test_one_anchored_phrase_separates_them_on_46_percent_of_days(a1) -> None:
    anchored = [
        dc_replace(m, valid_from=datetime(2025, 8, 2, tzinfo=UTC))
        if "before the move" in m.content
        else m
        for m in a1
    ]
    differ, total = _sweep(anchored)
    assert (differ, total) == (250, 549)
    assert round(differ / total, 2) == 0.46


def test_an_open_interval_reads_as_still_true(a1) -> None:
    """Nothing says the cycling stopped, only that a later memory has a train."""
    cycling = next(m for m in a1 if "cycle to work" in m.content)
    assert cycling.valid_to is None
    assert held_at(cycling, NOW)


def test_believed_at_is_the_belief_axis_only(a1) -> None:
    northwind = next(m for m in a1 if "data engineer at Northwind" in m.content)
    assert believed_at(northwind, JUNE_2025)
    assert not believed_at(northwind, NOW)
    assert held_at(northwind, JUNE_2025)
