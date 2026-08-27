"""Reference solution."""

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
        """Do the three stores agree about what exists and what is retired?

        Run after every write. A hybrid store that is never checked is three
        stores that have quietly stopped describing the same world.
        """
        out: list[Divergence] = []
        rows = self.rows.all()
        row_ids = {m.id for m in rows}

        missing = row_ids - set(self.vectors.vectors)
        if missing:
            out.append(Divergence("vector", f"{len(missing)} rows have no vector"))

        retired = {m.id for m in rows if not m.is_live}
        if retired - self.vectors.tombstoned:
            out.append(
                Divergence("tombstone",
                           f"{len(retired - self.vectors.tombstoned)} retired rows "
                           "are still servable from the vector index")
            )

        graphed = {m.id for group in self.graph.memories_by_entity.values() for m in group}
        expected = {m.id for m in rows if m.entities}
        if graphed != expected:
            out.append(Divergence("graph", f"{len(expected - graphed)} linked rows missing"))
        return out
