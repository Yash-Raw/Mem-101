"""Lab: filter, then rank.

    uv run python curriculum/intermediate/scopes-and-namespaces/lab/lab.py
"""
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
        """TODO: may a reader in this namespace see this memory?

        A None field means "any". A memory with no agent set is visible to
        every agent within the same user. Different users never mix.
        """
        raise NotImplementedError("implement Namespace.admits")


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
    """TODO: return memories visible to `scope` that belong to a DIFFERENT user.

    Not "everything this reader cannot see" -- narrowing to one agent is a
    relevance choice, not a leak. Crossing a user boundary is the thing that
    must never happen.
    """
    raise NotImplementedError("implement leak_check")


def rank_then_filter(memories: list[Memory], scope: Scope, k: int = 5) -> list[Memory]:
    """The wrong order, for contrast. Indistinguishable until it isn't."""
    from memlab.eval.exam import QUESTION
    from memlab.retrieve.embedding import EmbeddingRetriever

    hits = EmbeddingRetriever().search(QUESTION, memories, Scope(user=scope.user), k=k)
    ns = namespace_for(scope)
    return [h.memory for h in hits if ns.admits(h.memory)]


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import get
    from memlab.store.jsonl import JsonlStore

    store = JsonlStore("/tmp/memlab-scopes.jsonl")
    store.clear()
    ingest(store, Scope(user="priya"), get("intermediate"))
    memories = store.all()

    print("namespaces in the store:")
    for key, group in sorted(partition(memories).items()):
        print(f"   {key:<28} {len(group)}")

    print("\nwho sees what:")
    for scope in (
        Scope(user="priya"),
        Scope(user="priya", agent="calendar-agent"),
        Scope(user="sam"),
    ):
        seen = visible(memories, scope)
        leaked = leak_check(memories, scope)
        label = f"{scope.user}/{scope.agent or '*'}"
        print(f"   {label:<28} sees {len(seen):>2}   leak set: {len(leaked)}")

    hearsay = [m for m in memories if "Berlin" in m.content]
    for m in hearsay:
        print(f"\nthe hearsay row:\n   {m.content}")
        print(f"   namespace={m.scope.agent}  speaker={m.provenance.speaker}  "
              f"authority={m.provenance.authority}")
    print("\nVisible, and not believed. Two different mechanisms.")


if __name__ == "__main__":
    main()
