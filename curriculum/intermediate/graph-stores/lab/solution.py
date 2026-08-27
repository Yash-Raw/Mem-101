"""Reference solution."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from memlab.types import Memory


@dataclass
class EntityGraph:
    nodes: set[str] = field(default_factory=set)
    memories_by_entity: dict[str, list[Memory]] = field(default_factory=lambda: defaultdict(list))
    edges: set[tuple[str, str]] = field(default_factory=set)

    def build(self, memories: list[Memory]) -> EntityGraph:
        for m in memories:
            for e in m.entities:
                self.nodes.add(e)
                self.memories_by_entity[e].append(m)
            # An edge exists where one memory mentions two entities. That is
            # the only entity-to-entity relation this schema can express.
            linked = sorted(set(m.entities))
            for i, a in enumerate(linked):
                for b in linked[i + 1:]:
                    self.edges.add((a, b))
        return self

    def about(self, entity: str, live_only: bool = True) -> list[Memory]:
        """One hop: everything known about this entity."""
        found = self.memories_by_entity.get(entity, [])
        return [m for m in found if m.is_live] if live_only else list(found)

    def neighbours(self, entity: str) -> set[str]:
        return {b for a, b in self.edges if a == entity} | {a for a, b in self.edges if b == entity}

    def shape(self) -> dict[str, int]:
        """What the data actually supports -- the number that decides the question."""
        return {
            "nodes": len(self.nodes),
            "entity_edges": len(self.edges),
            "max_hops": 1 if self.nodes and not self.edges else (2 if self.edges else 0),
        }
