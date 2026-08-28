"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from memlab.store.scopes import Namespace, partition
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
    counts = {k: len(v) for k, v in partition(memories).items()}
    agent_spaces = [k for k in counts if k.split("/")[1] != "*"]
    user_space = [k for k in counts if k.split("/")[1] == "*"]

    if not agent_spaces:
        topology = Topology.SHARED
    elif not user_space:
        topology = Topology.PRIVATE
    else:
        topology = Topology.HIERARCHICAL
    return Shape(namespaces=counts, topology=topology)


def readable(memories: list[Memory], scope: Scope, topology: Topology) -> list[Memory]:
    """What a reader in `scope` sees under a given topology.

    The comparison this function exists for is what each shape *costs*, which
    is the number of memories a reader can no longer reach -- not a diagram.
    """
    if topology == Topology.SHARED:
        return [m for m in memories if m.scope.user == scope.user]

    if topology == Topology.PRIVATE:
        # Only this writer's own namespace. A user reading their own store
        # under PRIVATE sees nothing any agent contributed.
        return [
            m
            for m in memories
            if m.scope.user == scope.user and m.scope.agent == scope.agent
        ]

    # HIERARCHICAL and BLACKBOARD share a read rule -- the user-level
    # namespace plus your own. They differ on the *write* side, which is
    # where the distinction is worth having and where this function cannot
    # see it.
    ns = Namespace(user=scope.user, agent=scope.agent)
    return [m for m in memories if ns.admits(m)]
