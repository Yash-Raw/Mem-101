"""Lab: read the event clock off the sentence -- and know when not to.

    uv run python curriculum/advanced/relative-time-resolution/lab/lab.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum

from memlab.types import Memory


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
    raise NotImplementedError("implement classify")


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
    raise NotImplementedError("implement resolve")


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


GOLD = {
    "before the move": datetime(2025, 8, 2, tzinfo=UTC),
    "left Northwind Labs last month": datetime(2025, 12, 1, tzinfo=UTC),
    "gluten intolerance last week": datetime(2026, 5, 8, tzinfo=UTC),
    "since March 2026": datetime(2026, 3, 1, tzinfo=UTC),
}
SWEEP_FROM, SWEEP_TO = datetime(2025, 3, 1, tzinfo=UTC), datetime(2026, 9, 1, tzinfo=UTC)


def _sweep(memories):
    from memlab.temporal.validity import as_of

    differ, total, day = 0, 0, SWEEP_FROM
    while day < SWEEP_TO:
        total += 1
        if {m.id for m in as_of(memories, day)} != {
            m.id for m in as_of(memories, day, believed_at_time=day)
        }:
            differ += 1
        day += timedelta(days=1)
    return differ, total


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import _resolve_dedupe_reconcile_bitemporal, at
    from memlab.store.jsonl import JsonlStore
    from memlab.temporal.clocks import audit, event_start, turn_timestamps
    from memlab.types import Scope

    def build(pipeline, tag):
        store = JsonlStore(f"/tmp/memlab-anchor-{tag}.jsonl")
        store.clear()
        ingest(store, Scope(user="priya"), pipeline)
        return store.all()

    before = build(
        at("A1").with_stage(
            anchor=None, consolidate=_resolve_dedupe_reconcile_bitemporal
        ),
        "before",
    )
    after = build(at("A1"), "after")

    print("every relative reference in the corpus:\n")
    for m in sorted(before, key=lambda x: x.happened_at):
        r = classify(m)
        if r.anchor is Anchor.NONE:
            continue
        note = f"  <- {r.reason}" if r.reason else ""
        print(f"   {r.anchor.value:9} {r.phrase[:20]:22} {m.content[:44]}{note}")

    print("\n   resolved against gold.yml:\n")
    print(f"   {'phrase':34}{'resolved':13}{'gold':13}{'error':>7}")
    for fragment, truth in GOLD.items():
        m = next(x for x in after if fragment in x.content)
        got = event_start(m)
        print(f"   {fragment[:32]:34}{got.date()!s:13}{truth.date()!s:13}"
              f"{(got - truth).days:>6}d")

    print(f"\n   axes disagree on: {_sweep(before)[0]} of {_sweep(before)[1]} days"
          f"  ->  {_sweep(after)[0]} of {_sweep(after)[1]}")

    ts = turn_timestamps()
    a = audit(after, ts)
    anchored = [m for m in after if m.valid_from]
    print(f"\n   memories anchored: {len(anchored)}; the audit reports "
          f"{a.genuinely_distinct} derived")
    for m in anchored:
        if event_start(m).isoformat()[:19] in ts:
            print(f"   the missing one resolves to a write instant: "
                  f"{str(event_start(m))[:16]}  {m.content[:40]}")

    procedure = next(m for m in after if "weekly report" in m.content)
    print(f"\n   the procedure step, untouched: {procedure.valid_from is None}")


if __name__ == "__main__":
    main()
