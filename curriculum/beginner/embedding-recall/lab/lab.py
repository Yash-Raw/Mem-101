"""Lab: what is cosine similarity actually measuring?

    uv run python curriculum/beginner/embedding-recall/lab/lab.py
"""
from __future__ import annotations

from memlab.types import Memory, Scope


def search(query: str, memories: list[Memory], scope: Scope, k: int = 5) -> list[tuple[float, Memory]]:
    """TODO: filter by scope FIRST, then embed, score, sort, and cut to k.

    The order matters. If you score before filtering, a store holding several
    users leaks between them -- and the failure is silent.
    """
    raise NotImplementedError("implement search")


def most_similar_pairs(memories: list[Memory], top: int = 5) -> list[tuple[float, Memory, Memory]]:
    """TODO: score every pair of memories against each other, highest first.

    Use itertools.combinations. Cache the vectors -- content is immutable.
    Look hard at what comes out on top.
    """
    raise NotImplementedError("implement most_similar_pairs")


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-embed.jsonl")
    store.clear()
    ingest(store, scope)
    memories = store.all()

    print("search('what should I not eat?'):\n")
    for score, m in search("what should I not eat?", memories, scope, k=4):
        print(f"  {score:.3f}  {m.content}")

    print("\nmost similar PAIRS in the whole store:\n")
    for score, a, b in most_similar_pairs(memories, top=7):
        print(f"  {score:.3f}  {a.content[:36]:<36} | {b.content[:36]}")

    print("\nA duplicate, a retraction, a refinement, a contradiction --")
    print("and one score band holding all of them.")


if __name__ == "__main__":
    main()
