"""Storing the embedding, and the problem that creates.

Retrieval currently computes an embedding for every memory on every query --
**2N calls per query**, 1,480 of them on a 740-memory store. Memory content is
immutable, so each of those vectors is valid for the life of the record and is
being thrown away and recomputed thousands of times.

Caching it is easy. What makes this a lesson is what a cached vector means when
the memory it describes stops being true.

`Memory.id` is content-addressed, so an edit produces a different id and a
different cache entry -- content can never go stale. But **supersession does not
change the id**: `invalid_at` is set, the content is untouched, and the vector
stays perfectly valid for a belief nobody should be retrieving. A cache keyed on
content is therefore correct about text and silent about truth, which is exactly
the shape of bug this course keeps finding.

So the index carries a tombstone: the vector survives (audit and as-of queries
need it), and `live_ids` decides what a default search may see.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..llm.fake import cosine, embed_text
from ..types import Memory


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
