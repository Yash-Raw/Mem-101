"""Collapsing restatements of the same fact.

Idempotency and deduplication sound like the same thing and solve different
problems. Idempotency stops the *same turn* being processed twice -- it is why
`Memory.id` is derived from content plus source. Deduplication handles the same
*fact* arriving from different turns, which idempotency cannot see, because the
source differs and so does the id.

Priya's store has exactly that: sessions 8 and 9 both yield
`Priya works at Calico Systems`, from different sentences on different days.
Two records, identical content, different ids, cosine 1.000.

The rule here is deliberately strict, because the cost of the two mistakes is
not symmetric. A missed duplicate wastes a slot. A wrong merge destroys a
distinction -- and the near-miss cases in this corpus are `is vegetarian` /
`is pescatarian` (a refinement) and `is leaving Northwind` / `left Northwind`
(two reports of one event), neither of which is a duplicate and both of which
score high enough to be tempting.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import combinations

from ..llm.fake import cosine, embed_text
from ..types import Memory

# High on purpose. Everything below this is a *relationship*, not a repetition,
# and naming relationships is conflict detection's job -- see I4.
DUPLICATE_THRESHOLD = 0.95


@dataclass
class Merge:
    kept: Memory
    dropped: Memory
    similarity: float

    @property
    def reason(self) -> str:
        return f"identical restatement ({self.similarity:.3f})"


def _eligible(a: Memory, b: Memory) -> bool:
    """Only same-type, same-entity, both-live memories can be duplicates.

    Type matters most: an event and the state it produced score high and are
    doing different jobs. `Priya was diagnosed with a gluten intolerance` and
    `Priya has a gluten intolerance` are 0.739 apart and must both survive.
    """
    return (
        a.type is b.type
        and a.is_live
        and b.is_live
        and a.scope.user == b.scope.user
        and set(a.entities) == set(b.entities)
    )


def duplicate_pairs(
    memories: list[Memory], threshold: float = DUPLICATE_THRESHOLD
) -> list[Merge]:
    vectors = {m.id: embed_text(m.content) for m in memories}
    found = []
    for a, b in combinations(memories, 2):
        if not _eligible(a, b):
            continue
        score = cosine(vectors[a.id], vectors[b.id])
        if score >= threshold:
            # Keep the earlier assertion: it is when the fact first became known.
            first, second = sorted((a, b), key=lambda m: (m.happened_at or m.recorded_at))
            found.append(Merge(kept=first, dropped=second, similarity=score))
    return found


def dedupe(memories: list[Memory]) -> list[Memory]:
    """Collapse restatements, corroborating what survives.

    An independent restatement is evidence, so the survivor's confidence rises.
    That is the one piece of information a merge produces rather than destroys.
    """
    merges = duplicate_pairs(memories)
    dropped = {m.dropped.id for m in merges}
    corroborated = {m.kept.id: m for m in merges}

    out = []
    for memory in memories:
        if memory.id in dropped:
            continue
        if memory.id in corroborated:
            memory = replace(memory, confidence=min(1.0, memory.confidence + 0.1))
        out.append(memory)
    return out
