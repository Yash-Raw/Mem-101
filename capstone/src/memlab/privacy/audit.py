"""Proving a deletion, when the proof cannot be the data.

`deletion-that-actually-deletes` removed a record from three structures. Asked
to demonstrate that, the obvious move is to keep a copy of what was deleted --
which is the one thing the request forbade.

So a deletion receipt records everything except the content:

    the id                 content-addressed, so it *is* a fingerprint
    where it was found     per structure, zeroes included
    when, and on whose say  the request, its session, its timestamp
    what remains            a re-scan, run after, that must come back empty

The id is the interesting one. `Memory.id` is a SHA-256 of user, type,
content and source, truncated -- so it proves *which* record was deleted to
anyone holding the original, and reveals nothing to anyone who is not. The
property the store has had since Beginner for deduplication turns out to be
the one that makes an audit trail possible without retaining the data.

Retention is the other half. A receipt kept forever is a permanent record
that a person asked to be forgotten, which is its own disclosure -- so the
receipt has an expiry, and `expired` is a question you can ask it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ..types import Memory

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
        return original.id == self.memory_id


def rescan(memories: list[Memory], fingerprint: str, extra=()) -> int:
    """Anything still carrying the deleted id, anywhere it was supposed to go.

    Takes ids rather than content on purpose. Searching for the deleted text
    means holding the deleted text, and an audit that requires keeping a copy
    of what was erased has not erased it.
    """
    found = sum(1 for m in memories if m.id == fingerprint)
    for structure in extra:
        found += sum(1 for m in structure if m.id == fingerprint)
    return found


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
    return Receipt(
        memory_id=target.id,
        kind=kind,
        requested_by=f"user request, session {session}",
        requested_at=requested_at,
        deleted_at=deleted_at,
        structures=dict(structures),
        residue=residue,
    )
