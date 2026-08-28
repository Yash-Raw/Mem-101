"""Lab: price each topology by what a reader loses.

    uv run python curriculum/advanced/memory-topologies/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from memlab.types import Memory, Scope


class Topology(str, Enum):
    """`str`-backed, like `MemoryType`, so `==` holds across module copies.

    A lab imports its own `Topology` and the reference solution imports
    another; `is` between two enum classes with the same members is always
    False, and the symptom is every topology quietly behaving like the
    default branch. The codebase already uses str-backed enums for exactly
    this reason.
    """

    PRIVATE = "private"
    SHARED = "shared"
    HIERARCHICAL = "hierarchical"
    BLACKBOARD = "blackboard"


@dataclass(frozen=True)
class Shape:
    """What the store's namespaces actually look like."""

    namespaces: dict[str, int]
    topology: Topology

    @property
    def agents(self) -> int:
        return sum(1 for k in self.namespaces if k.split("/")[1] != "*")


def shape(memories: list[Memory]) -> Shape:
    """Read the topology off the data rather than off the design document."""
    raise NotImplementedError("implement shape")


def readable(memories: list[Memory], scope: Scope, topology: Topology) -> list[Memory]:
    """What a reader in `scope` sees under a given topology.

    The comparison this function exists for is what each shape *costs*, which
    is the number of memories a reader can no longer reach -- not a diagram.
    """
    raise NotImplementedError("implement readable")


PII = ("47 Halloway Road", "07700 900412")
ORDER = (Topology.PRIVATE, Topology.HIERARCHICAL, Topology.SHARED)


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-topology.jsonl")
    store.clear()
    ingest(store, scope, at("A3"))
    memories = store.all()

    found = shape(memories)
    print(f"the shape nobody chose: {found.topology.value}\n")
    for key, count in sorted(found.namespaces.items()):
        print(f"   {key:28} {count}")

    readers = [
        ("the user", scope),
        ("calendar-agent", Scope(user="priya", agent="calendar-agent")),
        ("travel-agent", Scope(user="priya", agent="travel-agent")),
    ]
    print(f"\n   {'reader':34}{'private':>9}{'hierarchical':>14}{'shared':>8}")
    for label, reader in readers:
        counts = [len(readable(memories, reader, t)) for t in ORDER]
        print(f"   {label:34}{counts[0]:>9}{counts[1]:>14}{counts[2]:>8}")

    print()
    travel = Scope(user="priya", agent="travel-agent")
    for topology in ORDER:
        seen = readable(memories, travel, topology)
        leaked = [m for m in seen if any(k in m.content for k in PII)]
        print(f"   travel-agent under {topology.value:14} sees {len(seen):3} memories, "
              f"{len(leaked)} carrying PII")
        for m in leaked:
            print(f"        {m.content}")


if __name__ == "__main__":
    main()
