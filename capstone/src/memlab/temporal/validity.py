"""As-of queries on two axes.

`two-clocks` measured that the record carries four instants and uses two.
This module is the query that makes the other two worth populating: what the
store holds to have been true at an event time, as believed at a belief time.

    as_of(memories, when)                       what was true then
    as_of(memories, when, believed_at=t)        ...as the store saw it at t

The second parameter is the one that surprises people. `live_only` -- the
filter every read path has applied since I4 -- is a belief-time filter with
its clock pinned to now. Asking a question about the past through it answers
with the present, silently.
"""
from __future__ import annotations

from datetime import datetime

from ..types import Memory
from .clocks import event_end, event_start


def held_at(m: Memory, when: datetime) -> bool:
    """Was this fact true at `when`, on the event axis?

    An open interval -- `valid_to` unset -- means "still true as far as anyone
    said". That is the honest reading: nothing in the corpus says the cycling
    stopped, only that a later memory describes a train.
    """
    start = event_start(m)
    if start is None or start > when:
        return False
    end = event_end(m)
    return end is None or end > when


def believed_at(m: Memory, when: datetime) -> bool:
    """Did the store hold this belief at `when`, on the belief axis?"""
    if m.recorded_at > when:
        return False
    return m.invalid_at is None or m.invalid_at > when


def as_of(
    memories: list[Memory],
    when: datetime,
    believed_at_time: datetime | None = None,
) -> list[Memory]:
    """Facts true at `when`, optionally as the store saw things at another time.

    Omit `believed_at_time` and you get the store's *current* account of the
    past -- corrections included. Pass it and you get the account it would
    have given then, mistakes and all. Both are legitimate; conflating them is
    how an audit trail stops being one.
    """
    out = [m for m in memories if held_at(m, when)]
    if believed_at_time is not None:
        out = [m for m in out if believed_at(m, believed_at_time)]
    return out


def overlapping(
    memories: list[Memory], start: datetime, end: datetime
) -> list[Memory]:
    """Facts true at any point in [start, end).

    A question carries the precision it was asked at. "In 2025" names a year,
    and answering it at 2025-01-01 -- the instant a year-precision parse
    defaults to -- silently asks about the least likely day the person meant.
    An interval question deserves an interval answer.
    """
    out = []
    for m in memories:
        vs = event_start(m)
        if vs is None or vs >= end:
            continue
        ve = event_end(m)
        if ve is None or ve > start:
            out.append(m)
    return out


def changed_between(
    memories: list[Memory], start: datetime, end: datetime
) -> list[tuple[Memory, str]]:
    """What moved on either axis in the window, and which axis moved.

    Returns (memory, axis) with axis in {"became true", "stopped being true",
    "believed", "retired"}. Four kinds of change, because there are two axes
    and each has two ends -- and a changelog that reports only "retired" tells
    you when the system noticed, never when the world moved.
    """
    events: list[tuple[Memory, str]] = []
    for m in memories:
        vs, ve = event_start(m), event_end(m)
        if vs and start <= vs < end:
            events.append((m, "became true"))
        if ve and start <= ve < end:
            events.append((m, "stopped being true"))
        if start <= m.recorded_at < end:
            events.append((m, "believed"))
        if m.invalid_at and start <= m.invalid_at < end:
            events.append((m, "retired"))
    return sorted(events, key=lambda e: _stamp(e[0], e[1]))


def _stamp(m: Memory, axis: str) -> datetime:
    return {
        "became true": event_start(m),
        "stopped being true": event_end(m),
        "believed": m.recorded_at,
        "retired": m.invalid_at,
    }[axis]
