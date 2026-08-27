"""Reference solution."""

from __future__ import annotations

from memlab.evolve.conflict import slot_of
from memlab.retrieve.embedding import Hit
from memlab.retrieve.query import slots_for


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
