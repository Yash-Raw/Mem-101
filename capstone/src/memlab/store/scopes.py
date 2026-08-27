"""Namespaces: who can see which memories.

Scope is a correctness boundary, not an index hint. The failure it prevents is
silent: rank across tenants and the wrong person's memory simply scores well and
gets injected into a prompt. Nothing errors, nothing logs, and the only signal
is a user seeing a fact about a stranger.

So the rule is **filter, then rank** -- never rank, then filter -- and the
filter is a hard predicate over structured keys rather than anything the
embedding participates in.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..types import Memory, Scope

SHARED = "*"


@dataclass(frozen=True)
class Namespace:
    """A visibility rule. `None` on a field means 'any'."""

    user: str
    agent: str | None = None
    session: str | None = None

    @property
    def key(self) -> str:
        """Stable partition key. This is what a real store shards on."""
        return "/".join([self.user, self.agent or SHARED, self.session or SHARED])

    def admits(self, memory: Memory) -> bool:
        if memory.scope.user != self.user:
            return False
        if self.agent is not None and memory.scope.agent not in (None, self.agent):
            return False
        return not (
            self.session is not None
            and memory.scope.session not in (None, self.session)
        )


def namespace_for(scope: Scope) -> Namespace:
    return Namespace(user=scope.user, agent=scope.agent, session=scope.session)


def visible(memories: list[Memory], scope: Scope) -> list[Memory]:
    """The hard filter. Everything a reader is allowed to see, unranked."""
    ns = namespace_for(scope)
    return [m for m in memories if ns.admits(m)]


def partition(memories: list[Memory]) -> dict[str, list[Memory]]:
    """Group by namespace key -- how a store would actually shard."""
    out: dict[str, list[Memory]] = {}
    for m in memories:
        out.setdefault(namespace_for(m.scope).key, []).append(m)
    return out


def leak_check(memories: list[Memory], scope: Scope) -> list[Memory]:
    """Memories visible to `scope` that belong to a DIFFERENT user.

    Deliberately narrower than "everything this reader cannot see". Narrowing
    to one agent's namespace is a relevance choice -- the excluded rows are not
    a leak, they are simply out of scope. Crossing a user boundary is the thing
    that must never happen, and it is the only one worth asserting in
    production, because it is the only one with no other signal.
    """
    return [m for m in visible(memories, scope) if m.scope.user != scope.user]
