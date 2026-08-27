"""Filter, then rank -- and the order is the lesson.

Beginner filtered on owner. I4 added validity. I5 gave memories tiers and
nothing consulted them. This is where the read path finally uses everything the
write path spent five modules recording.

    scope      whose memories -- a correctness boundary (I2)
    validity   retired beliefs never compete (I4)
    tier       demoted memories are out of the way (I5)

Then, and only then, ranking. Filtering after ranking means foreign or dead
memories consume top-k slots and get dropped, so recall silently depends on
what else is in the database.

`search` is the composed read path: filter, formulate the query, gather
candidates by slot AND by similarity, rank, merge. It is the function
`Pipeline.rank` points at.
"""
from __future__ import annotations

from ..types import Memory, Scope, Tier
from .embedding import Hit
from .hybrid import rank as hybrid_rank
from .query import formulate, in_slots, slots_for


def eligible(memories: list[Memory], scope: Scope, retrievable_only: bool = True) -> list[Memory]:
    """The hard filters, before anything is scored."""
    out = [m for m in memories if m.scope.matches(scope) and m.is_live]
    if retrievable_only and any(m.tier is Tier.LONG_TERM for m in out):
        out = [m for m in out if m.tier is Tier.LONG_TERM]
    return out


def _merge(lists: list[list[Hit]], k: int) -> list[Hit]:
    """Guarantee each sub-question its best answer, then fill by score.

    Two obvious strategies both fail. Global top-k lets the better-matching
    half take every slot -- the diet question outscores the employer question
    on every row. Strict round-robin is worse: it hands the employer half a
    third and a fifth slot for `Priya is a staff engineer` while the diet half
    still has a gluten intolerance waiting.

    So: one guaranteed slot per sub-question, and the rest to whatever scores
    highest. Every question gets an answer; no question gets padding.
    """
    merged: list[Hit] = []
    seen: set[str] = set()

    for hits in lists:                      # guarantee
        if hits and hits[0].memory.id not in seen:
            seen.add(hits[0].memory.id)
            merged.append(hits[0])

    rest = sorted(
        (h for hits in lists for h in hits if h.memory.id not in seen),
        key=lambda h: -h.score,
    )
    for hit in rest:                        # fill
        if len(merged) >= k:
            break
        if hit.memory.id not in seen:
            seen.add(hit.memory.id)
            merged.append(hit)
    return merged[:k]


def search(
    query: str, memories: list[Memory], scope: Scope, k: int = 5, index=None
) -> list[Hit]:
    pool = eligible(memories, scope)
    if not pool:
        return []

    per_query: list[list[Hit]] = []
    for sub in formulate(query, scope):
        # Candidates by SLOT as well as by similarity. The slot set catches
        # facts that answer the question without sharing its vocabulary --
        # "gluten intolerance" against "what should I not eat".
        by_slot = in_slots(pool, slots_for(sub))
        candidates = {m.id: m for m in [*by_slot, *pool]}.values()
        per_query.append(hybrid_rank(sub, list(candidates), scope, k=k, index=index))

    return _merge(per_query, k)
