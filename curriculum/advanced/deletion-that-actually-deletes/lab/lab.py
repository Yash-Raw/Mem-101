"""Lab: resolve a deletion request, then reach every structure.

    uv run python curriculum/advanced/deletion-that-actually-deletes/lab/lab.py
"""

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
    raise NotImplementedError("implement resolve")


def cascade(target: Memory, memories: list[Memory], vectors, sqlite) -> Cascade:
    """Remove a memory from every structure that holds it or derives from it.

    Every count is returned, including the zeroes. `temporal-knowledge-graphs`
    measured that a cascade reporting only what it removed is indistinguishable
    from one whose edges point nowhere, and deletion is the operation where
    that distinction is legally load-bearing.
    """
    raise NotImplementedError("implement cascade")


def purge(target: Memory, memories: list[Memory]) -> list[Memory]:
    """The primary store, with the target and anything derived from it gone.

    Not supersession. Everything else in this course retires rather than
    destroys, and this is the one operation where the record must actually
    stop existing -- which is why it needed its own vocabulary rather than
    another `invalid_at`.
    """
    raise NotImplementedError("implement purge")


def main() -> None:
    from datetime import UTC

    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.privacy.classify import Kind
    from memlab.store.jsonl import JsonlStore
    from memlab.store.sqlite import SqliteStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    pipeline = at("A3")
    store = JsonlStore("/tmp/memlab-delete.jsonl")
    store.clear()
    ingest(store, scope, pipeline)
    memories = store.all()
    pipeline.vectors.index(memories)
    sqlite = SqliteStore("/tmp/memlab-delete.db")
    sqlite.clear()
    sqlite.add(memories)

    request = Request(
        text="forget my old address, I don't want that stored anywhere",
        session=13,
        at=datetime(2026, 6, 20, tzinfo=UTC),
    )

    word = sum(1 for m in memories if "address" in m.content.lower())
    print(f"resolving by the word she used:\n   records containing "
          f"'address': {word}\n")

    found = resolve(request, memories, Kind.ADDRESS)
    print(f"resolving by label: {len(found.candidates)} candidate(s), "
          f"actionable={found.actionable}")
    print(f"   {found.reason}")
    for candidate in found.candidates:
        print(f"      {candidate.content}")

    target = found.candidates[0]
    result = cascade(target, memories, pipeline.vectors, sqlite)
    kept = purge(target, memories)
    print(f"\ncascade: primary={result.primary}  sqlite={result.sqlite}  "
          f"vectors={result.vectors}  derived={result.derived}  "
          f"summaries={result.summaries}   total={result.total}")
    print("gone from: "
          f"primary={not any('Halloway' in m.content for m in kept)}  "
          f"sqlite={not any('Halloway' in m.content for m in sqlite.all())}  "
          f"vectors={not pipeline.vectors.holds(target.id)}")


if __name__ == "__main__":
    main()
