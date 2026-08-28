"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

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
    return m.valid_to


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
    total = len(memories)
    with_event = [m for m in memories if event_start(m) is not None]
    copied = [
        m for m in with_event if event_start(m).isoformat()[:19] in turn_timestamps
    ]
    return ClockAudit(
        total=total,
        with_event_time=len(with_event),
        copied_from_the_turn=len(copied),
        genuinely_distinct=len(with_event) - len(copied),
        with_event_end=sum(1 for m in memories if event_end(m) is not None),
    )


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
