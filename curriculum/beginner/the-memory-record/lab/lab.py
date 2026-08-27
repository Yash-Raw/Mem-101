"""Lab: retire a belief without destroying it.

    uv run python curriculum/beginner/the-memory-record/lab/lab.py
"""
from __future__ import annotations

from datetime import UTC, datetime

from memlab.types import Memory, MemoryType, Provenance, Scope


def supersede(old: Memory, new: Memory, at: datetime) -> tuple[Memory, Memory]:
    """TODO: return (retired_old, new).

    Use old.supersede(by=..., at=...). Do not delete anything.
    """
    raise NotImplementedError("implement supersede")


def as_of(memories: list[Memory], when: datetime) -> list[Memory]:
    """TODO: return the memories that were live at `when`.

    A memory is live at `when` if it had already become true and had not yet
    been retired. Both clocks matter.
    """
    raise NotImplementedError("implement as_of")


def employer(memories: list[Memory]) -> str:
    hits = [m for m in memories if "works at" in m.content]
    return hits[0].content if hits else "(unknown)"


def main() -> None:
    scope = Scope(user="priya")
    old = Memory(
        content="Priya works at Northwind Labs",
        type=MemoryType.SEMANTIC, scope=scope,
        provenance=Provenance(source_id="s1:2025-03-04T09:12:00Z", speaker="user"),
        happened_at=datetime(2025, 3, 4, tzinfo=UTC),
    )
    new = Memory(
        content="Priya works at Calico Systems",
        type=MemoryType.SEMANTIC, scope=scope,
        provenance=Provenance(source_id="s8:2025-12-08T09:00:00Z", speaker="user"),
        happened_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    retired, current = supersede(old, new, at=datetime(2026, 1, 1, tzinfo=UTC))
    store = [retired, current]

    print("store holds both records; neither was deleted\n")
    for when in ("2025-06-01", "2026-06-01"):
        t = datetime.fromisoformat(when).replace(tzinfo=UTC)
        print(f"  as_of({when}) -> {employer(as_of(store, t))}")

    print(f"\nretired record still present: {retired.content!r}")
    print(f"  invalid_at    {retired.invalid_at.date()}")
    print(f"  superseded_by {retired.superseded_by}")


if __name__ == "__main__":
    main()
