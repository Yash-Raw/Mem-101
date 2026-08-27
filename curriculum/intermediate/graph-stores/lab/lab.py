"""Lab: measure the graph before adopting one.

    uv run python curriculum/intermediate/graph-stores/lab/lab.py
"""

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
        """TODO: what does the data actually support?

        nodes, entity_edges, and max_hops -- 2 if there are edges, 1 if there
        are nodes but no edges, 0 if empty.

        This is the method that decides whether the rest of the module should
        exist for your data.
        """
        raise NotImplementedError("implement shape")


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-graph.jsonl")
    store.clear()
    ingest(store, scope, at("I6"))
    memories = store.all()

    graph = EntityGraph().build(memories)
    print(f"graph shape: {graph.shape()}")
    print(f"  nodes: {sorted(graph.nodes)}")

    for node in sorted(graph.nodes):
        live = graph.about(node)
        every = graph.about(node, live_only=False)
        print(f"\n  about({node!r}): {len(live)} live of {len(every)} total")
        for m in every:
            print(f"     live={m.is_live!s:<5} {m.content[:50]}")
        print(f"  neighbours({node!r}): {graph.neighbours(node) or 'none'}")

    print("\nOne node, no edges. The only traversal is entity -> its memories,")
    print("which is a dictionary lookup wearing a graph's clothes.")


if __name__ == "__main__":
    main()
