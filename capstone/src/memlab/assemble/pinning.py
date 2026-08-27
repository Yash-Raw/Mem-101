"""What must never be dropped -- as a budget policy, not a list of topics.

`budgeted-forgetting` ended on a specific failure. Protecting dietary facts from
eviction saved the diet and evicted the employer instead, because a protected-
class list defends only the classes someone thought of, and the facts a question
depends on vary per question.

So the policy here is not "diet is important". It is:

    **every slot the question asked about must be covered in context.**

That is general -- it is derived from the query, not from a topic list -- and it
is exactly the thing score-order cannot express. `Priya is a staff engineer`
outscores `Priya has a gluten intolerance` on every signal the ranker has, and
the ranker is right: it *is* a better answer to the employer question. It is
also the second answer to a question already answered, and it is taking the
tokens the diet question's third fact needs.

The ranker orders within a question. Pinning allocates across them.
"""
from __future__ import annotations

from ..evolve.conflict import slot_of
from ..retrieve.embedding import Hit
from ..retrieve.query import slots_for


def required(hits: list[Hit], per_slot: int = 3) -> list[Hit]:
    """Hits that cover the slots their own sub-questions asked about.

    Breadth first across slots, then depth up to `per_slot` -- so a question
    with three relevant facts is not starved by a question with one.
    """
    wanted: dict[str, set[str]] = {}
    for hit in hits:
        wanted.setdefault(hit.query or "", set()).update(slots_for(hit.query or ""))

    by_slot: dict[str, list[Hit]] = {}
    for hit in hits:
        slot = slot_of(hit.memory)
        if slot and any(slot in slots for slots in wanted.values()):
            by_slot.setdefault(slot, []).append(hit)

    out: list[Hit] = []
    for depth in range(per_slot):
        for slot in sorted(by_slot):
            group = by_slot[slot]
            if depth < len(group):
                out.append(group[depth])
    return out


def unpinned(hits: list[Hit], pinned: list[Hit]) -> list[Hit]:
    ids = {h.memory.id for h in pinned}
    return [h for h in hits if h.memory.id not in ids]
