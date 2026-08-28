"""Deriving higher-order beliefs, and refusing to derive most of them.

I3 measured that similarity cannot tell a refinement from a corroboration from
a contradiction -- 0.669, 0.505, 0.439, no threshold between them -- which is
why `evolve/promote.py` promotes nothing. Point it at reflection and it fails
the same way, harder:

    20 candidate pairs, and the highest-scoring is
        0.557  Priya drinks tea + Priya drinks three coffees a day

which is not an insight. It is the contradiction I4 already arbitrated. Second
place pairs tea with her employer; third pairs her job title with her
preference for short answers. **14 of 20 pair facts from unrelated slots**, and
the first genuine dietary relation sits sixth.

So candidates come from structure -- live beliefs sharing a SLOT -- and the
work is in what gets thrown away. Reflection composes; it does not write. A
composed insight can be checked against its sources, and a generated one is a
sentence nobody can trace.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from ..evolve.conflict import slot_of
from ..types import Memory, MemoryType, Scope


class Refusal(Enum):
    """Why a group was not turned into a belief."""

    THIRD_PARTY = "third party"      # the facts are about someone else
    TOO_FEW = "too few"              # one belief is not a synthesis


@dataclass(frozen=True)
class Group:
    slot: str
    members: tuple[Memory, ...]
    refusal: Refusal | None = None

    @property
    def ok(self) -> bool:
        return self.refusal is None


def groups(memories: list[Memory], scope: Scope) -> list[Group]:
    """Live beliefs sharing a slot, with the reason each is or is not usable."""
    by_slot: dict[str, list[Memory]] = defaultdict(list)
    for m in memories:
        if m.type is MemoryType.SEMANTIC and slot_of(m):
            by_slot[slot_of(m)].append(m)

    out = []
    for slot, members in sorted(by_slot.items()):
        live = tuple(m for m in members if m.is_live)
        out.append(Group(slot=slot, members=live, refusal=_refuse(live)))
    return out


def _refuse(live: tuple[Memory, ...]) -> Refusal | None:
    """Why not to compose. Retired members are not a reason -- they are simply
    not members: the composite is built from what is live, so the history the
    slot carries is untouched and `temporal-questions` still answers it.
    """
    if len(live) < 2:
        return Refusal.TOO_FEW

    # The one that catches you. Slots are keyed on what is claimed, not on who
    # it is claimed about -- so `occupation_other` groups two facts about
    # Priya's partner, and composing them attributes a night-shift nursing job
    # to Priya. Any third-party entity disqualifies the group.
    if any(m.entities for m in live):
        return Refusal.THIRD_PARTY

    return None


def compose(group: Group, scope: Scope) -> Memory:
    """One belief from several, traceable to every source.

    Template, not generation. A composed insight can be checked against its
    members; a written one is a sentence with no way back to the evidence,
    and this is the stage where an unsupported claim would enter the store
    looking exactly like a supported one.
    """
    ordered = sorted(group.members, key=lambda m: m.happened_at or m.recorded_at)
    content = f"{group.slot}: " + "; ".join(m.content for m in ordered)
    return Memory(
        content=content,
        type=MemoryType.SEMANTIC,
        scope=scope,
        provenance=ordered[-1].provenance,
        happened_at=ordered[-1].happened_at,
        recorded_at=ordered[-1].recorded_at,
        # Every source, so `cascade` can retire this the moment one goes.
        derived_from=tuple(sorted(m.id for m in ordered)),
        confidence=min(m.confidence for m in ordered),
    )


def reflect(memories: list[Memory], scope: Scope) -> list[Memory]:
    """The derived beliefs, and nothing else."""
    return [compose(g, scope) for g in groups(memories, scope) if g.ok]
