"""Reference solution."""
from __future__ import annotations

from itertools import combinations

from memlab.llm.fake import cosine, embed_text
from memlab.types import Memory, Scope


def search(query: str, memories: list[Memory], scope: Scope, k: int = 5) -> list[tuple[float, Memory]]:
    """Scope first -- it is a correctness boundary, not an optimisation."""
    candidates = [m for m in memories if m.scope.matches(scope)]
    q = embed_text(query)
    scored = [(cosine(q, embed_text(m.content)), m) for m in candidates]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:k]


def most_similar_pairs(memories: list[Memory], top: int = 5) -> list[tuple[float, Memory, Memory]]:
    """Score every pair against every other. The top of this list is instructive."""
    vecs = {m.id: embed_text(m.content) for m in memories}
    pairs = [
        (cosine(vecs[a.id], vecs[b.id]), a, b)
        for a, b in combinations(memories, 2)
    ]
    pairs.sort(key=lambda t: t[0], reverse=True)
    return pairs[:top]
