"""A store per memory type, and the cost of keeping them agreeing.

The textbook architecture: vectors for semantic recall, a relational store for
scoped and time-bounded queries, a graph for entities. Each is genuinely better
at its job than the others.

What the diagrams leave out is that one write now touches three stores, and one
**supersession** has to be reflected in all of them or the system holds a belief
in one place and its retraction in another. That is not a performance cost, it
is a correctness cost, and it is the reason to reach for a single store until
the pressure is real.

This module is deliberately small: it fans a write out and then checks the
stores agree. The checking is the interesting half.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..types import Memory, Scope
from .graph import EntityGraph
from .sqlite import SqliteStore
from .vector import VectorIndex


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
