"""Lab: prove a deletion without keeping what was deleted.

    uv run python curriculum/advanced/rtbf-and-auditability/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from memlab.types import Memory

# How long a receipt outlives the deletion it records. Long enough to answer
# an audit, short enough that the fact of the request is not itself permanent.
RETENTION = timedelta(days=365)


@dataclass(frozen=True)
class Receipt:
    """Proof that a record was deleted, holding none of what it said."""

    memory_id: str
    kind: str
    requested_by: str
    requested_at: datetime
    deleted_at: datetime
    structures: dict[str, int] = field(default_factory=dict)
    residue: int = 0

    @property
    def complete(self) -> bool:
        """Did the re-scan come back empty?"""
        return self.residue == 0

    @property
    def reached(self) -> tuple[str, ...]:
        return tuple(sorted(k for k, v in self.structures.items() if v))

    def expired(self, now: datetime, retention: timedelta = RETENTION) -> bool:
        return now - self.deleted_at > retention

    def proves(self, original: Memory) -> bool:
        """Does this receipt describe that record?

        Answerable by anyone holding the original and by nobody else, which
        is what lets the receipt be shown without re-disclosing the content.
        """
        raise NotImplementedError("implement Receipt.proves")


def rescan(memories: list[Memory], fingerprint: str, extra=()) -> int:
    """Anything still carrying the deleted id, anywhere it was supposed to go.

    Takes ids rather than content on purpose. Searching for the deleted text
    means holding the deleted text, and an audit that requires keeping a copy
    of what was erased has not erased it.
    """
    raise NotImplementedError("implement rescan")


def issue(
    target: Memory,
    kind: str,
    session: int,
    requested_at: datetime,
    deleted_at: datetime,
    structures: dict[str, int],
    residue: int,
) -> Receipt:
    """Write the receipt.

    The request's *text* is deliberately not a parameter. Storing what the
    user said in order to prove you honoured it is the same mistake as
    storing what you deleted -- a session number and a timestamp locate the
    turn without reproducing it.
    """
    raise NotImplementedError("implement issue")


def main() -> None:
    from datetime import UTC

    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.privacy.classify import Kind
    from memlab.privacy.delete import Request, cascade, purge, resolve
    from memlab.store.jsonl import JsonlStore
    from memlab.store.sqlite import SqliteStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    now = datetime(2026, 6, 20, tzinfo=UTC)
    pipeline = at("A3")
    store = JsonlStore("/tmp/memlab-audit.jsonl")
    store.clear()
    ingest(store, scope, pipeline)
    memories = store.all()
    pipeline.vectors.index(memories)
    sqlite = SqliteStore("/tmp/memlab-audit.db")
    sqlite.clear()
    sqlite.add(memories)

    request = Request(text="forget my old address", session=13, at=now)
    target = resolve(request, memories, Kind.ADDRESS).candidates[0]
    result = cascade(target, memories, pipeline.vectors, sqlite)
    kept = purge(target, memories)

    residue = rescan(kept, target.id, extra=[sqlite.all()])
    receipt = issue(
        target,
        Kind.ADDRESS.value,
        request.session,
        request.at,
        now,
        {
            "primary": result.primary,
            "sqlite": result.sqlite,
            "vectors": result.vectors,
            "derived": result.derived,
            "summaries": result.summaries,
        },
        residue,
    )

    print(f"receipt for {receipt.memory_id}")
    print(f"   kind      : {receipt.kind}")
    print(f"   requested : {receipt.requested_at.date()}   "
          f"deleted: {receipt.deleted_at.date()}")
    print(f"   by        : {receipt.requested_by}")
    print(f"   structures: {receipt.structures}")
    print(f"   reached   : {receipt.reached}")
    print(f"   residue   : {receipt.residue}   complete={receipt.complete}")

    other = next(m for m in kept if m.id != target.id)
    print(f"\n   proves the original record   {receipt.proves(target)}")
    print(f"   proves a different record    {receipt.proves(other)}")
    print(f"   receipt contains the content {'Halloway' in str(receipt)}")

    for days in (100, 366):
        print(f"\n   expired after {days} days: "
              f"{receipt.expired(now + timedelta(days=days))}")


if __name__ == "__main__":
    main()
