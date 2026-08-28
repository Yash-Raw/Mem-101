"""Two clocks in the record; one of them was never running."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.fixtures import load_turns
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

audit = _solution.audit
event_start = _solution.event_start
event_end = _solution.event_end
turn_timestamps = _solution.turn_timestamps


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("tc") / "m.jsonl")
    ingest(s, Scope(user="priya"), at("I8"))  # the system Level 2 shipped
    return s.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.audit(memories, turn_timestamps())


def test_every_event_time_is_the_write_clock(memories) -> None:
    """37 of 37. The field is populated and carries no information."""
    a = audit(memories, turn_timestamps())
    assert (a.total, a.with_event_time) == (37, 37)
    assert a.copied_from_the_turn == 37
    assert a.genuinely_distinct == 0
    assert a.share_copied == 1.0


def test_and_nothing_records_that_anything_stopped(memories) -> None:
    a = audit(memories, turn_timestamps())
    assert a.with_event_end == 0
    assert all(event_end(m) is None for m in memories)


def test_counting_only_user_turns_gives_the_comfortable_answer(memories) -> None:
    """34 of 37, 92%, and three interesting exceptions that are not exceptions.

    The agent stamps its own clock exactly as the extractor does. The number
    was not wrong; the population it was measured over was.
    """
    b = audit(memories, {t["ts"][:19] for t in load_turns()})
    assert b.copied_from_the_turn == 34
    assert round(b.share_copied, 2) == 0.92


def test_the_three_that_look_distinct_are_agent_writes(memories) -> None:
    users_only = {t["ts"][:19] for t in load_turns()}
    odd = [m for m in memories if event_start(m).isoformat()[:19] not in users_only]
    assert len(odd) == 3
    assert {m.provenance.speaker for m in odd} == {"calendar-agent", "travel-agent"}


@pytest.mark.parametrize(
    "fragment,truth,days",
    [
        ("before the move", datetime(2025, 8, 2, tzinfo=UTC), 249),
        ("left Northwind Labs last month", datetime(2025, 12, 1, tzinfo=UTC), 49),
        ("gluten intolerance last week", datetime(2026, 5, 8, tzinfo=UTC), 7),
    ],
)
def test_the_error_runs_forwards(memories, fragment, truth, days) -> None:
    """Always late, never early -- in a system whose rule is recency wins."""
    m = next(x for x in memories if fragment in x.content)
    assert (event_start(m) - truth).days == days


def test_event_start_falls_back_so_old_records_still_answer(memories) -> None:
    """valid_from is unset everywhere until A1's parser lands; happened_at
    carries the query until then, at whatever precision it happens to have."""
    assert all(m.valid_from is None for m in memories)
    assert all(event_start(m) == m.happened_at for m in memories)
