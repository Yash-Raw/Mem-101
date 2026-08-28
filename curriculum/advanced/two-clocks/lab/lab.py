"""Lab: find out which of the two clocks is actually running.

    uv run python curriculum/advanced/two-clocks/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from memlab.types import Memory


def event_start(m: Memory) -> datetime | None:
    """When the fact became true. Falls back to when it was asserted."""
    return m.valid_from or m.happened_at


def event_end(m: Memory) -> datetime | None:
    """When the fact stopped being true -- not when we stopped believing it.

    A fact can stop being true without anyone noticing (`valid_to` set,
    `invalid_at` still None), and a belief can be retired while the fact it
    described remains true (a mistaken supersession). Collapsing the two
    makes both cases unreportable.
    """
    raise NotImplementedError("implement event_end")


def belief_start(m: Memory) -> datetime:
    return m.recorded_at


def belief_end(m: Memory) -> datetime | None:
    return m.invalid_at


@dataclass(frozen=True)
class ClockAudit:
    """How many of the two clocks are actually measuring something."""

    total: int
    with_event_time: int
    copied_from_the_turn: int
    genuinely_distinct: int
    with_event_end: int

    @property
    def share_copied(self) -> float:
        return self.copied_from_the_turn / self.total if self.total else 0.0


def audit(memories: list[Memory], turn_timestamps: set[str]) -> ClockAudit:
    """Count the records whose event time is just the time they were said.

    `turn_timestamps` is every turn instant in the corpus, to second
    precision. A record whose event time is one of them learned nothing from
    the language -- the extractor copied the clock it already had.
    """
    raise NotImplementedError("implement audit")


def turn_timestamps() -> set[str]:
    """Every instant anything was *written* at, to second precision.

    Agent writes belong in here as much as user turns. Leave them out and the
    three memories a calendar agent contributed look like they carry a
    genuinely distinct event time, when the agent is doing exactly what the
    extractor does -- stamping the record with its own clock.
    """
    from memlab.fixtures import load_agent_writes, load_turns

    return {t["ts"][:19] for t in load_turns()} | {
        w["ts"][:19] for w in load_agent_writes()
    }


RELATIVE = [
    ("before the move", datetime(2025, 8, 2, tzinfo=UTC)),
    ("left Northwind Labs last month", datetime(2025, 12, 1, tzinfo=UTC)),
    ("gluten intolerance last week", datetime(2026, 5, 8, tzinfo=UTC)),
]


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.fixtures import load_turns
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    store = JsonlStore("/tmp/memlab-clocks.jsonl")
    store.clear()
    ingest(store, Scope(user="priya"), at("I8"))  # the system Level 2 shipped
    memories = store.all()

    a = audit(memories, turn_timestamps())
    print("which clock is running?\n")
    print(f"  total memories                       {a.total:4d}")
    print(f"  with an event time                   {a.with_event_time:4d}")
    print(f"    ...just the instant it was written {a.copied_from_the_turn:4d}   ({a.share_copied:.0%})")
    print(f"    ...derived from the language       {a.genuinely_distinct:4d}")
    print(f"  with an event end                    {a.with_event_end:4d}")

    print("\n  and the phrases nobody parsed:\n")
    print(f"  {'stored':<46}{'happened_at':>13}{'actually':>13}{'off by':>9}")
    for fragment, truth in RELATIVE:
        m = next(x for x in memories if fragment in x.content)
        off = (event_start(m) - truth).days
        print(f"  {m.content[:44]:<46}{event_start(m).date()!s:>13}"
              f"{truth.date()!s:>13}{off:>7}d")

    users_only = {t["ts"][:19] for t in load_turns()}
    b = audit(memories, users_only)
    print(f"\n  counting only user turns: {b.copied_from_the_turn} of {b.total}"
          f" ({b.share_copied:.0%}) -- the comfortable answer")


if __name__ == "__main__":
    main()
