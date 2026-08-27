"""Lab: cache the vectors, then find what the cache cannot see.

    uv run python curriculum/intermediate/vector-stores-for-mutable-data/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass, field

from memlab.llm.fake import cosine, embed_text
from memlab.types import Memory


@dataclass
class VectorIndex:
    """Content-addressed embedding cache with tombstones."""

    vectors: dict[str, list[float]] = field(default_factory=dict)
    tombstoned: set[str] = field(default_factory=set)
    computed: int = 0
    served: int = 0

    def index(self, memories: list[Memory]) -> int:
        """TODO: embed anything new, tombstone anything retired.

        Key on m.id -- content-addressed, so an edit is a different entry.
        A memory with `is_live` False keeps its vector AND gets tombstoned:
        the vector is correct, the belief is not.

        Return how many vectors were newly computed.
        """
        raise NotImplementedError("implement index")

    def vector_for(self, memory: Memory) -> list[float]:
        if memory.id in self.vectors:
            self.served += 1
            return self.vectors[memory.id]
        self.vectors[memory.id] = embed_text(memory.content)
        self.computed += 1
        return self.vectors[memory.id]

    def live(self, memories: list[Memory]) -> list[Memory]:
        return [m for m in memories if m.id not in self.tombstoned]

    def search(self, query: str, memories: list[Memory], k: int = 5) -> list[tuple[float, Memory]]:
        """One embed call for the query. Zero for the corpus, once warm."""
        q = embed_text(query)
        self.computed += 1
        scored = [(cosine(q, self.vector_for(m)), m) for m in self.live(memories)]
        scored.sort(key=lambda pair: -pair[0])
        return scored[:k]

    @property
    def stats(self) -> dict[str, int]:
        return {
            "vectors": len(self.vectors),
            "tombstoned": len(self.tombstoned),
            "computed": self.computed,
            "served_from_cache": self.served,
        }


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.eval.exam import QUESTION
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-vector.jsonl")
    store.clear()
    ingest(store, scope, at("I6"))
    memories = store.all()

    index = VectorIndex()
    computed = index.index(memories)
    print(f"indexing {len(memories)} memories: {computed} vectors computed")
    print(f"  tombstoned (retired beliefs): {len(index.tombstoned)}")
    print(f"  visible to a default search:  {len(index.live(memories))}\n")

    for _ in range(3):
        index.search(QUESTION, memories, k=5)
    print(f"after 3 queries: {index.stats}")
    print(f"  uncached, the same 3 queries cost {3 * 2 * len(memories)} embed calls\n")

    print("uncached cost at replicated scale (illustrative -- the property is the 2N):")
    for size, calls in replication_curve(memories):
        print(f"   store {size:>5}   {calls:>5} embed calls per query")
    print()

    retired = next(m for m in memories if not m.is_live and "Northwind" in m.content)
    print("the vector a content-addressed cache cannot invalidate:")
    print(f"   {retired.content}")
    print("   content unchanged, id unchanged, vector still correct")
    print(f"   invalid_at={retired.invalid_at.date()}  tombstoned={retired.id in index.tombstoned}")


if __name__ == "__main__":
    main()


def replication_curve(memories: list[Memory], multiples=(1, 20, 50)) -> list[tuple[int, int]]:
    """(store size, uncached embed calls per query) at replicated scale.

    Illustrative only -- the corpus is replicated, so twenty identical Priyas
    would break entity resolution and deduplication. The PROPERTY is what to
    read: uncached cost is 2N per query, and N is everything ever written.
    """
    from dataclasses import replace as _replace

    out = []
    for mult in multiples:
        big = list(memories)
        for i in range(1, mult):
            big += [
                _replace(
                    m,
                    provenance=_replace(m.provenance, source_id=f"{m.provenance.source_id}#{i}"),
                    id="",
                )
                for m in memories
            ]
        out.append((len(big), 2 * len(big)))
    return out
