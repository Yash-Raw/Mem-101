"""Reading the event clock off the sentence.

`validity-intervals` measured that the bi-temporal model is degenerate until
something moves an event time off the write clock, and that anchoring a single
phrase separates the two axes on 46% of the corpus. This is that parser.

Six memories in the corpus carry a relative reference and they fall into four
classes, only one of which is arithmetic:

    OFFSET     "last week", "last month"     turn clock minus a delta
    INTERVAL   "since March 2026"            opens valid_from, leaves the end
    EVENT      "before the move"             needs another memory to resolve
    LITERAL    "diff against last week"      not a time reference at all

The last class is the one that costs you. It is a step inside a taught
procedure, and a parser that fires on every match rewrites the recipe.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum

from ..types import Memory, MemoryType


class Anchor(Enum):
    OFFSET = "offset"
    INTERVAL = "interval"
    EVENT = "event"
    LITERAL = "literal"
    NONE = "none"


# Ordered: the first match wins, and EVENT is tested before OFFSET because
# "used to cycle before the move" contains no offset but does contain a
# reference that arithmetic would silently skip.
_EVENT = re.compile(r"\b(before|after) the (\w+)", re.IGNORECASE)
_INTERVAL = re.compile(
    r"\bsince ((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*)\s*"
    r"((?:19|20)\d{2})?",
    re.IGNORECASE,
)
# Two kinds of offset, and conflating them is a 19-day error. "Last week" is
# a span of days and subtracting seven of them is right. "Last month" names a
# calendar unit -- December, not "thirty days ago" -- and the answer inherits
# that precision, so it resolves to the start of that month rather than to a
# day in the middle of it.
_OFFSET_DAYS = {
    r"\blast week\b": timedelta(days=7),
    r"\byesterday\b": timedelta(days=1),
    r"\btwo weeks ago\b": timedelta(days=14),
}
_OFFSET_CALENDAR = {
    r"\blast month\b": "month",
    r"\blast year\b": "year",
}
_OFFSET = {**_OFFSET_DAYS, **_OFFSET_CALENDAR}
_MONTHS = {
    m: i + 1
    for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])
}


@dataclass(frozen=True)
class Resolution:
    anchor: Anchor
    phrase: str = ""
    valid_from: datetime | None = None
    reason: str = ""


def classify(memory: Memory) -> Resolution:
    """Which kind of reference this is -- including "none of them"."""
    text = memory.content

    # A procedure's steps are instructions, not claims about when the
    # procedure is true. "diff against last week" is the recipe.
    if memory.type is MemoryType.PROCEDURAL:
        found = _first_offset(text)
        if found:
            return Resolution(
                Anchor.LITERAL,
                found[0],
                reason="a step inside a procedure, not a claim about when",
            )
        return Resolution(Anchor.NONE)

    event = _EVENT.search(text)
    if event:
        return Resolution(
            Anchor.EVENT,
            event.group(0),
            reason=f"needs the date of '{event.group(2)}' from another memory",
        )

    interval = _INTERVAL.search(text)
    if interval:
        return Resolution(Anchor.INTERVAL, interval.group(0))

    found = _first_offset(text)
    if found:
        return Resolution(Anchor.OFFSET, found[0])

    return Resolution(Anchor.NONE)


def _first_offset(text: str) -> tuple[str, timedelta | str] | None:
    for pattern, delta in _OFFSET.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(0), delta
    return None


def _previous(unit: str, said_at: datetime) -> datetime:
    """The start of the previous calendar month or year."""
    midnight = {"hour": 0, "minute": 0, "second": 0, "microsecond": 0}
    if unit == "year":
        return said_at.replace(year=said_at.year - 1, month=1, day=1, **midnight)
    year = said_at.year - 1 if said_at.month == 1 else said_at.year
    month = 12 if said_at.month == 1 else said_at.month - 1
    return said_at.replace(year=year, month=month, day=1, **midnight)


def resolve(memory: Memory, pool: list[Memory]) -> Memory:
    """Set `valid_from` from the language, or leave the memory untouched.

    Untouched is the common and correct outcome. A parser that always
    produces a date is a parser that invents them.
    """
    r = classify(memory)
    said_at = memory.happened_at or memory.recorded_at

    if r.anchor is Anchor.OFFSET:
        _, delta = _first_offset(memory.content)
        if isinstance(delta, str):
            return replace(memory, valid_from=_previous(delta, said_at))
        return replace(memory, valid_from=said_at - delta)

    if r.anchor is Anchor.INTERVAL:
        m = _INTERVAL.search(memory.content)
        month = _MONTHS[m.group(1)[:3].lower()]
        year = int(m.group(2)) if m.group(2) else said_at.year
        return replace(memory, valid_from=datetime(year, month, 1, tzinfo=said_at.tzinfo))

    if r.anchor is Anchor.EVENT:
        when = _event_date(_EVENT.search(memory.content).group(2), pool)
        if when is None:
            return memory  # unresolvable is a legitimate answer
        return replace(memory, valid_from=when)

    return memory


# The events a conversation refers to by name, and the memory that dates each.
# Small and explicit: a general "find the event" is a research problem, and
# guessing is worse than declining -- see the lesson.
_EVENT_MARKERS = {
    "move": ("lives at", "moved house"),
}


def _event_date(noun: str, pool: list[Memory]) -> datetime | None:
    markers = _EVENT_MARKERS.get(noun.lower())
    if not markers:
        return None
    dated = [
        m.happened_at
        for m in pool
        if any(mk in m.content for mk in markers) and m.happened_at
    ]
    return min(dated) if dated else None


def anchor_all(memories: list[Memory], _turns: dict | None = None) -> list[Memory]:
    """Pipeline stage: resolve every relative reference that can be resolved."""
    return [resolve(m, memories) for m in memories]
