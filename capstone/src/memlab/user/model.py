"""What the store believes about the user, as a model rather than a list.

The naive model is "every live semantic memory" -- 19 statements on this
corpus. It is wrong in two ways that a count of statements hides:

    about someone else (entities set)     2     Samira's job, in a model of Priya
    claiming no attribute to key on       6     "Priya mostly does pipeline work"

So a model keyed on SLOT holds **six** attributes about Priya, and six
statements cannot enter it at all. That second number is the interesting one:
they are not noise -- *"Priya is debugging a Spark job"* is a real fact the
user stated -- they simply describe nothing the system has a name for.

Volatility is read from the supersession history rather than asserted. An
attribute that has been replaced has demonstrated it can change; one that
never has is, so far, stable. "So far" is doing real work: on this corpus
`commute` looks stable and only because nobody has moved twice.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ..evolve.conflict import slot_of
from ..types import Memory, MemoryType, Scope


@dataclass(frozen=True)
class Attribute:
    """One slot of the model: what is believed now, and how settled it is."""

    slot: str
    beliefs: tuple[Memory, ...]
    superseded: int

    @property
    def volatile(self) -> bool:
        """Has this attribute ever been replaced?"""
        return self.superseded > 0

    @property
    def values(self) -> tuple[str, ...]:
        return tuple(m.content for m in self.beliefs)


@dataclass(frozen=True)
class UserModel:
    scope: Scope
    attributes: dict[str, Attribute]
    unkeyed: tuple[Memory, ...]     # true, stated, and about no modelled attribute
    third_party: tuple[Memory, ...]  # about someone else entirely

    @property
    def stable(self) -> tuple[str, ...]:
        return tuple(sorted(k for k, a in self.attributes.items() if not a.volatile))

    @property
    def volatile(self) -> tuple[str, ...]:
        return tuple(sorted(k for k, a in self.attributes.items() if a.volatile))


def build(memories: list[Memory], scope: Scope) -> UserModel:
    """Assemble the model, and keep what would not fit rather than dropping it.

    `unkeyed` and `third_party` are returned, not discarded. A model that
    silently omits a third of what it was built from reports the same shape
    as one with nothing to omit, and the omission is where the next question
    lives.
    """
    semantic = [m for m in memories if m.type is MemoryType.SEMANTIC]
    live = [m for m in semantic if m.is_live]

    third_party = tuple(m for m in live if m.entities)
    mine = [m for m in live if not m.entities]

    grouped: dict[str, list[Memory]] = defaultdict(list)
    for m in mine:
        if slot_of(m):
            grouped[slot_of(m)].append(m)

    # Supersessions are counted over the whole slot, retired records included,
    # and only for beliefs about this user -- a partner changing jobs is not
    # evidence that the user's employer is volatile.
    retired: dict[str, int] = defaultdict(int)
    for m in semantic:
        if not m.is_live and not m.entities and slot_of(m):
            retired[slot_of(m)] += 1

    return UserModel(
        scope=scope,
        attributes={
            slot: Attribute(slot=slot, beliefs=tuple(ms), superseded=retired[slot])
            for slot, ms in sorted(grouped.items())
        },
        unkeyed=tuple(m for m in mine if not slot_of(m)),
        third_party=third_party,
    )
