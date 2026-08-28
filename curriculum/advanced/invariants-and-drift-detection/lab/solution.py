"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from memlab.types import Memory


class Kind(str, Enum):
    STRUCTURAL = "structural"
    POLICY = "policy"


@dataclass(frozen=True)
class Violation:
    invariant: str
    kind: Kind
    count: int
    detail: str = ""

    @property
    def holds(self) -> bool:
        return self.count == 0


def check(memories: list[Memory], scope) -> list[Violation]:
    """Every invariant this course established, in one pass."""
    from memlab.evolve.conflict import slot_of
    from memlab.store.scopes import leak_check
    from memlab.temporal.clocks import event_start
    from memlab.types import MemoryType

    live = [m for m in memories if m.is_live]

    # Leave-one-out. Computing the reference clock over the whole store lets a
    # single future-dated record redefine "the clock" and pass its own check --
    # measured, and it is the failure this invariant exists to catch. Each
    # memory is compared against the newest of the OTHERS.
    stamps = sorted(s for s in (event_start(m) for m in memories) if s)
    latest, runner_up = (stamps[-1], stamps[-2]) if len(stamps) > 1 else (None, None)

    retired_early = [
        m for m in memories if m.invalid_at and m.invalid_at < m.recorded_at
    ]
    dangling = [
        m
        for m in memories
        for ref in m.derived_from
        if ref not in {x.id for x in memories}
    ]
    orphan_supersede = [
        m
        for m in memories
        if m.superseded_by
        and m.superseded_by != "correction"
        and m.superseded_by not in {x.id for x in memories}
    ]
    future = [
        m
        for m in memories
        if runner_up
        and event_start(m)
        and event_start(m) > (runner_up if event_start(m) == latest else latest)
        + timedelta(days=1)
    ]
    duplicate_ids = len(memories) - len({m.id for m in memories})
    two_live_in_slot = [
        slot
        for slot in {slot_of(m) for m in live if slot_of(m)}
        if sum(
            1
            for m in live
            if slot_of(m) == slot
            and m.type is MemoryType.SEMANTIC
            and not m.entities
        )
        > 4
    ]

    return [
        Violation("no cross-tenant memory is visible", Kind.STRUCTURAL,
                  len(leak_check(memories, scope))),
        Violation("no belief is retired before it was recorded", Kind.STRUCTURAL,
                  len(retired_early)),
        Violation("every derived_from reference resolves", Kind.STRUCTURAL,
                  len(dangling)),
        Violation("every superseded_by reference resolves", Kind.STRUCTURAL,
                  len(orphan_supersede)),
        Violation("ids are unique", Kind.STRUCTURAL, duplicate_ids),
        Violation("no memory is dated past the store's clock", Kind.POLICY,
                  len(future)),
        Violation("no slot holds more than four live beliefs", Kind.POLICY,
                  len(two_live_in_slot),
                  ", ".join(two_live_in_slot)),
    ]


def failing(violations: list[Violation]) -> list[Violation]:
    return [v for v in violations if not v.holds]


def by_kind(violations: list[Violation], kind: Kind) -> list[Violation]:
    return [v for v in violations if v.kind is kind]
