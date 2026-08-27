"""Reference solution."""
from __future__ import annotations

from memlab.llm.fake import cosine, embed_text
from memlab.types import Memory, Scope, Tier


def eligible(memories: list[Memory], scope: Scope, retrievable_only: bool = True) -> list[Memory]:
    out = [m for m in memories if m.scope.matches(scope) and m.is_live]
    if retrievable_only and any(m.tier is Tier.LONG_TERM for m in out):
        out = [m for m in out if m.tier is Tier.LONG_TERM]
    return out


def rank_only(query: str, pool: list[Memory]) -> list[tuple[float, Memory]]:
    q = embed_text(query)
    scored = [(cosine(q, embed_text(m.content)), m) for m in pool]
    scored.sort(key=lambda p: -p[0])
    return scored


def rank_then_filter(
    query: str, memories: list[Memory], scope: Scope, k: int = 5
) -> list[Memory]:
    """The wrong order. Returns fewer than k, unpredictably."""
    ranked = rank_only(query, [m for m in memories if m.scope.matches(scope)])
    top = [m for _, m in ranked[:k]]
    return [m for m in top if m.is_live and m.tier is Tier.LONG_TERM]


def employer_rank(query: str, pool: list[Memory]) -> int | None:
    return next(
        (i for i, (_, m) in enumerate(rank_only(query, pool), 1)
         if "works at Calico" in m.content),
        None,
    )
