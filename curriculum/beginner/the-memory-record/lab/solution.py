"""Reference solution."""
from __future__ import annotations

from datetime import datetime

from memlab.types import Memory


def supersede(old: Memory, new: Memory, at: datetime) -> tuple[Memory, Memory]:
    """Retire `old` in favour of `new`. Nothing is destroyed."""
    return old.supersede(by=new.id, at=at), new


def as_of(memories: list[Memory], when: datetime) -> list[Memory]:
    """What the system would have said was true at `when`.

    A memory counts if it had already become true (`happened_at <= when`) and
    had not yet been retired (`invalid_at` unset or later than `when`).
    """
    out = []
    for m in memories:
        if m.happened_at and m.happened_at > when:
            continue
        if m.invalid_at and m.invalid_at <= when:
            continue
        out.append(m)
    return out
