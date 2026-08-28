"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass

from memlab.types import Memory, Scope
from memlab.user.apply import apply
from memlab.user.model import UserModel, build


@dataclass(frozen=True)
class Coverage:
    """The model at one point in a conversation."""

    turn: int
    memories: int
    attributes: tuple[str, ...]

    @property
    def size(self) -> int:
        return len(self.attributes)


def growth(
    snapshots: list[tuple[int, list[Memory]]], scope: Scope
) -> list[Coverage]:
    """Model size after each of a sequence of stores."""
    return [
        Coverage(
            turn=turn,
            memories=len(memories),
            attributes=tuple(sorted(build(memories, scope).attributes)),
        )
        for turn, memories in snapshots
    ]


def answerable(model: UserModel, question: str, scope: Scope, needed) -> bool:
    """Whether the attributes this question reaches actually contain the facts.

    Distinct from "is the model complete". Coverage counts attributes; this
    reads their contents, and the two milestones are two turns apart on this
    corpus -- in the direction that makes a coverage check optimistic.
    """
    applied = apply(model, question, scope)
    text = " ".join(v for a in applied.asked for v in a.values)
    return all(fact in text for fact in needed)


def merged(memories: list[Memory], scope: Scope) -> UserModel:
    """The model a shared account produces: entity links discarded.

    Not a hypothetical. Two people already appear in this store, and the only
    thing keeping the second out of the first's model is the `entities` field
    I2 populates.
    """
    from dataclasses import replace

    return build([replace(m, entities=()) for m in memories], scope)
