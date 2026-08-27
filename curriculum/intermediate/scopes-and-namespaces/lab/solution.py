"""Reference solution."""
from __future__ import annotations

from dataclasses import dataclass

from memlab.types import Memory, Scope

SHARED = "*"


@dataclass(frozen=True)
class Namespace:
    user: str
    agent: str | None = None
    session: str | None = None

    @property
    def key(self) -> str:
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
    ns = namespace_for(scope)
    return [m for m in memories if ns.admits(m)]


def partition(memories: list[Memory]) -> dict[str, list[Memory]]:
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


def rank_then_filter(memories: list[Memory], scope: Scope, k: int = 5) -> list[Memory]:
    """The wrong order, for contrast. Indistinguishable until it isn't."""
    from memlab.eval.exam import QUESTION
    from memlab.retrieve.embedding import EmbeddingRetriever

    hits = EmbeddingRetriever().search(QUESTION, memories, Scope(user=scope.user), k=k)
    ns = namespace_for(scope)
    return [h.memory for h in hits if ns.admits(h.memory)]
