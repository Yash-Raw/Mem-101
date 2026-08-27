"""Reference solution."""

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
        """Embed anything new; tombstone anything retired. Returns new vectors."""
        added = 0
        for m in memories:
            if m.id not in self.vectors:
                self.vectors[m.id] = embed_text(m.content)
                self.computed += 1
                added += 1
            if m.is_live:
                self.tombstoned.discard(m.id)
            else:
                # Content unchanged, belief retired. The vector stays -- audit
                # needs it -- and default retrieval must not see it.
                self.tombstoned.add(m.id)
        return added

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
