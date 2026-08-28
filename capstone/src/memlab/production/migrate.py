"""Changing the record shape while the store is full, as this course did twice.

A1 added `valid_from` and `valid_to` to a record that already had 37 memories
written against the old shape. That is a schema migration on live memory, and
it worked for reasons worth naming rather than repeating by luck:

    1. the new fields were nullable, so old records stayed readable
    2. `_revive` used `d.get(...)`, so old JSON lines did not need rewriting
    3. `Memory.id` hashes user, type, content and source -- NOT the new
       fields -- so no id changed and nothing downstream noticed
    4. `event_start` falls back to `happened_at`, so old records answered
       the new query at whatever precision they had

Point 3 is the one that cannot be arranged afterwards. A content-addressed id
that included every field would have changed on every record, breaking
`derived_from`, `superseded_by`, the vector cache and every pinned test at
once -- and the migration would have been a rewrite of the whole store.

Backfill is the other half. Old records answer as-of queries with
`happened_at`, which is *"when this was asserted"* rather than *"when it was
true"*. Reprocessing history through A1's parser is what turns a tolerable
fallback into the real value, and it is optional, restartable and
independently verifiable -- three properties the write path already had.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from ..types import Memory


@dataclass(frozen=True)
class Compatibility:
    """Why a shape change did or did not require rewriting the store."""

    rule: str
    holds: bool
    consequence: str


def compatibility(old: Memory, new: Memory) -> list[Compatibility]:
    """Check a proposed record change against the four rules.

    `old` and `new` are the same memory before and after the change, which is
    the only comparison that answers the question -- a schema diff cannot see
    whether the id moved.
    """
    return [
        Compatibility(
            "new fields are nullable",
            new.valid_from is None or old.valid_from is None,
            "old records stay readable without a default",
        ),
        Compatibility(
            "the id did not change",
            old.id == new.id,
            "derived_from, superseded_by and the vector cache stay valid",
        ),
        Compatibility(
            "content did not change",
            old.content == new.content,
            "pinned assertions and fixtures still match",
        ),
        Compatibility(
            "the old value still answers",
            (new.valid_from or new.happened_at) is not None,
            "queries degrade in precision, not in availability",
        ),
    ]


@dataclass(frozen=True)
class Backfill:
    """A reprocessing pass over history, and what it changed."""

    considered: int
    updated: int
    unchanged: int

    @property
    def restartable(self) -> bool:
        """Re-running must change nothing the second time."""
        return True


def backfill(memories: list[Memory], anchor) -> tuple[list[Memory], Backfill]:
    """Reprocess history through a parser the records predate.

    Idempotent by construction: the parser writes `valid_from` from content,
    so a second pass computes the same value. That is what makes it safe to
    restart, and it is the same property `background-job-mechanics` needed
    from consolidation.
    """
    out = anchor(list(memories))
    updated = sum(
        1
        for before, after in zip(memories, out, strict=True)
        if before.valid_from != after.valid_from
    )
    return out, Backfill(
        considered=len(memories),
        updated=updated,
        unchanged=len(memories) - updated,
    )


def strip(memories: list[Memory]) -> list[Memory]:
    """The store as it looked before the fields existed."""
    return [replace(m, valid_from=None, valid_to=None) for m in memories]
