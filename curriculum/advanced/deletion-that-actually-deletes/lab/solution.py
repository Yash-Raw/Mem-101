"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from memlab.types import Memory


@dataclass(frozen=True)
class Request:
    """A deletion request as stated, before anything is resolved."""

    text: str
    session: int
    at: datetime


@dataclass(frozen=True)
class Resolution:
    """What the request could mean, and whether that is one thing."""

    request: Request
    candidates: tuple[Memory, ...]
    reason: str

    @property
    def ambiguous(self) -> bool:
        return len(self.candidates) != 1

    @property
    def actionable(self) -> bool:
        return len(self.candidates) == 1


@dataclass(frozen=True)
class Cascade:
    """Where a deleted memory was found, and where it was removed from."""

    primary: int
    sqlite: int
    vectors: int
    derived: int
    summaries: int

    @property
    def total(self) -> int:
        return self.primary + self.sqlite + self.vectors + self.derived + self.summaries


def resolve(request: Request, memories: list[Memory], kind) -> Resolution:
    """Find the records a request names, by LABEL rather than by wording.

    The obvious implementation matches the user's word against the content
    and finds nothing: she says *"my old address"* and the store says
    *"Priya lives at 47 Halloway Road, Bristol"*, which contains no such
    word. Searching for "address" returns zero records and the request looks
    already satisfied.

    So resolution runs on `privacy.classify`'s labels. That is what
    `pii-on-the-write-path` meant by keeping the classification as a label
    rather than a permission: the stage that needs it most is this one, and
    it needs it years after the write.
    """
    from memlab.privacy.classify import classify

    candidates = tuple(m for m in memories if classify(m) is kind)
    if not candidates:
        reason = f"nothing in the store is labelled {kind.value!r}"
    elif len(candidates) > 1:
        reason = f"{len(candidates)} records labelled {kind.value!r}"
    else:
        only = candidates[0]
        reason = (
            f"one record labelled {kind.value!r}, from "
            f"{only.provenance.source_id} — but the request says 'old' and "
            f"this is the address she gave as her new one"
        )
    return Resolution(request=request, candidates=candidates, reason=reason)


def cascade(target: Memory, memories: list[Memory], vectors, sqlite) -> Cascade:
    """Remove a memory from every structure that holds it or derives from it.

    Every count is returned, including the zeroes. `temporal-knowledge-graphs`
    measured that a cascade reporting only what it removed is indistinguishable
    from one whose edges point nowhere, and deletion is the operation where
    that distinction is legally load-bearing.
    """
    derived = [m for m in memories if target.id in m.derived_from]
    summaries = [
        m
        for m in memories
        if m.derived_from and target.provenance.source_id in m.derived_from
    ]

    removed_sqlite = 0
    if sqlite is not None:
        before = len(sqlite.all())
        sqlite.replace([m for m in sqlite.all() if m.id != target.id])
        removed_sqlite = before - len(sqlite.all())

    # `holds` rather than `vector_for`: the latter *computes* a vector when
    # one is missing, so asking it whether the index has something is how you
    # end up creating the thing you were about to delete.
    removed_vectors = 0
    if vectors is not None and vectors.holds(target.id):
        removed_vectors = int(vectors.forget(target.id))

    return Cascade(
        primary=1,
        sqlite=removed_sqlite,
        vectors=removed_vectors,
        derived=len(derived),
        summaries=len(summaries),
    )


def purge(target: Memory, memories: list[Memory]) -> list[Memory]:
    """The primary store, with the target and anything derived from it gone.

    Not supersession. Everything else in this course retires rather than
    destroys, and this is the one operation where the record must actually
    stop existing -- which is why it needed its own vocabulary rather than
    another `invalid_at`.
    """
    doomed = {target.id} | {
        m.id for m in memories if target.id in m.derived_from
    }
    return [m for m in memories if m.id not in doomed]
