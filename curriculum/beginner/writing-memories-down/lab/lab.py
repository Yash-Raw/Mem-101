"""Lab: what a duplicate actually costs.

    uv run python curriculum/beginner/writing-memories-down/lab/lab.py
"""
from __future__ import annotations

from memlab.extract.naive import extract
from memlab.fixtures import load_turns
from memlab.retrieve.embedding import EmbeddingRetriever
from memlab.store.jsonl import JsonlStore
from memlab.types import Memory, Scope

QUESTION = "where do I work?"


class IdempotentStore(JsonlStore):
    def add(self, memories: list[Memory]) -> int:
        """TODO: append only memories whose id is not already in the store.

        Return how many were actually written.
        """
        raise NotImplementedError("implement IdempotentStore.add")


class NaiveStore(JsonlStore):
    """Given, for contrast. Appends unconditionally."""

    def add(self, memories: list[Memory]) -> int:
        with self.path.open("a") as fh:
            for m in memories:
                fh.write(m.to_json() + "\n")
        return len(memories)


def ingest_all(store: JsonlStore, scope: Scope) -> int:
    written = 0
    for turn in load_turns(user_only=True):
        if turn["session"] < 14:
            written += store.add(extract(turn, scope))
    return written


def main() -> None:
    scope = Scope(user="priya")

    for label, cls in (("idempotent", IdempotentStore), ("naive", NaiveStore)):
        store = cls(f"/tmp/memlab-dupes-{label}.jsonl")
        store.clear()
        first = ingest_all(store, scope)
        second = ingest_all(store, scope)
        print(f"\n{label}: first ingest wrote {first}, second wrote {second} "
              f"-> {len(store.all())} total")

        hits = EmbeddingRetriever().search(QUESTION, store.all(), scope, k=5)
        seen: dict[str, int] = {}
        for h in hits:
            seen[h.memory.content] = seen.get(h.memory.content, 0) + 1
        dupes = {c: n for c, n in seen.items() if n > 1}
        print(f"  top-5 holds {len(set(seen))} distinct memories")
        for c, n in dupes.items():
            print(f"    x{n}  {c[:58]}")


if __name__ == "__main__":
    main()
