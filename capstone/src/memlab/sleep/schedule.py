"""When consolidation runs, and what decides.

`ingest()` consolidates once, at the end of the corpus -- which is only
possible because the corpus arrives all at once. Replay it a turn at a time,
the way a live system receives it, and the choice appears:

                                    runs   embed   cosine   wrong turns
    defer everything                   1      38      282            11
    consolidate every turn            25     503     1630             0

Both end at the same 30 live memories: consolidation is order-independent on
this corpus, which is what makes deferral safe at all. So the cost of
deferring is not compute. It is that the store is wrong in between.

The obvious gate is the memory's type -- standing beliefs get contradicted,
events do not. It barely helps: 24 of 35 memories are semantic and 18 of 24
turns write one, so the filter fires nearly always.

The gate that works is the one the write path already computes. A window only
opens when a turn claims a SLOT something live already claims -- which is the
same table I4 uses to generate conflict candidates, because it is the same
question asked one stage earlier.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..evolve.conflict import slot_of
from ..types import Memory, MemoryType


class Gate(Enum):
    NEVER = "never"        # defer everything to the batch
    ALWAYS = "always"      # consolidate on every turn
    TYPE = "type"          # ...when a standing belief was written
    CONTESTED = "contested"  # ...when the turn claims an occupied slot


@dataclass(frozen=True)
class Schedule:
    """What has to happen before the next turn is answered."""

    gate: Gate = Gate.CONTESTED
    inline_types: frozenset[MemoryType] = frozenset({MemoryType.SEMANTIC})

    @classmethod
    def default(cls) -> Schedule:
        return cls(gate=Gate.CONTESTED)

    @classmethod
    def never(cls) -> Schedule:
        return cls(gate=Gate.NEVER)

    @classmethod
    def always(cls) -> Schedule:
        return cls(gate=Gate.ALWAYS)

    @classmethod
    def by_type(cls) -> Schedule:
        return cls(gate=Gate.TYPE)

    def needs_inline(self, written: list[Memory], stored: list[Memory]) -> bool:
        """Does this turn's output have to be consolidated before we answer?

        `stored` is the store as it stood *before* this turn -- the slots
        already claimed. Passing the post-write store makes every turn
        contested by its own writes.
        """
        if self.gate is Gate.NEVER:
            return False
        if self.gate is Gate.ALWAYS:
            return True
        if self.gate is Gate.TYPE:
            return any(m.type in self.inline_types for m in written)

        held = {slot_of(m) for m in stored if m.is_live}
        held.discard(None)
        return any(slot_of(m) in held for m in written if slot_of(m) is not None)
