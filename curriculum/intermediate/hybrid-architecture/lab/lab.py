"""Lab: three stores, and keeping them agreeing.

    uv run python curriculum/intermediate/hybrid-architecture/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.store.graph import EntityGraph
from memlab.store.sqlite import SqliteStore
from memlab.store.vector import VectorIndex
from memlab.types import Memory, Scope


@dataclass
class Divergence:
    what: str
    detail: str


class HybridStore:
    """Fan-out over a relational store, a vector index and an entity graph."""

    def __init__(self, path: str = ":memory:") -> None:
        self.rows = SqliteStore(path)
        self.vectors = VectorIndex()
        self.graph = EntityGraph()

    def write(self, memories: list[Memory]) -> int:
        written = self.rows.add(memories)
        self.vectors.index(memories)
        self.graph = EntityGraph().build(self.rows.all())
        return written

    def eligible(self, scope: Scope) -> list[Memory]:
        """Rows filter, vectors tombstone. Both must agree."""
        return self.vectors.live(self.rows.eligible(scope))

    def check(self) -> list[Divergence]:
        """TODO: do the three stores agree about what exists and what is retired?

          vector    every row has a vector
          tombstone every retired row is tombstoned in the vector index
          graph     every entity-bearing row appears in the graph

        Return a Divergence per failure. Run after every write -- a hybrid
        store that is never checked is three stores that have quietly stopped
        describing the same world.
        """
        raise NotImplementedError("implement check")


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    source = JsonlStore("/tmp/memlab-hybrid-src.jsonl")
    source.clear()
    ingest(source, scope, at("I6"))
    memories = source.all()

    store = HybridStore()
    print(f"fan-out write: {store.write(memories)} rows")
    print(f"  eligible:     {len(store.eligible(scope))}")
    print(f"  graph shape:  {store.graph.shape()}")
    print(f"  divergences:  {store.check() or 'none -- all three stores agree'}\n")

    print("now break each arm of the contract in turn:\n")

    skipped = HybridStore()
    skipped.rows.add(memories)
    skipped.graph = type(store.graph)().build(memories)
    print(f"  vector index skipped -> {[d.what for d in skipped.check()]}")

    untombstoned = HybridStore()
    untombstoned.write(memories)
    untombstoned.vectors.tombstoned.clear()
    print(f"  tombstones cleared   -> {[d.what for d in untombstoned.check()]}")

    stale = HybridStore()
    stale.write(memories)
    stale.graph = type(store.graph)()
    print(f"  graph not rebuilt    -> {[d.what for d in stale.check()]}")


if __name__ == "__main__":
    main()
