"""Entities as nodes -- and an honest look at whether this corpus needs one.

Graph stores are the fashionable answer to agent memory, and the argument for
them is real: relations between entities are exactly what a row-oriented store
represents badly, and multi-hop questions ("who is Priya's partner and where
does she work?") are one traversal instead of several queries.

The argument only pays when there are relations to traverse. Built over Priya's
store, this graph has:

    1 entity node        samira, linked from 6 memories
    0 entity-to-entity edges

`St. Aubyn's` is not a node because it is on the `NOT_PEOPLE` stop list --
correctly, it is a hospital, and I2 put it there after watching it become a
person. So the only traversal available is entity -> its memories, which is a
dictionary lookup wearing a graph's clothes.

That is the lesson. A graph store is the right answer to a shape of data, and
recognising you do not have that shape is worth more than adopting it anyway.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ..types import Memory


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
