"""Reference solution."""

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
