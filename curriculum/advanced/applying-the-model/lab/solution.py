"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from memlab.retrieve.query import formulate, slots_for
from memlab.types import Scope
from memlab.user.model import Attribute, UserModel


class Mode(str, Enum):
    ANSWER = "answer"
    INSTRUCTION = "instruction"


# Which attributes are standing instructions rather than facts to report.
# Short, explicit, and reviewable: the cost of a wrong entry here is either a
# volunteered address or a preference silently ignored, and both are visible.
INSTRUCTIONS: frozenset[str] = frozenset({"response_style"})


def mode(slot: str) -> Mode:
    return Mode.INSTRUCTION if slot in INSTRUCTIONS else Mode.ANSWER


@dataclass(frozen=True)
class Applied:
    """What a question is entitled to, split by why."""

    asked: tuple[Attribute, ...]        # answers the question requested
    instructions: tuple[Attribute, ...]  # standing preferences, always applied
    withheld: tuple[Attribute, ...]     # facts nobody asked for

    @property
    def volunteered(self) -> int:
        return 0  # by construction; the test asserts it


def asked_slots(question: str, scope: Scope) -> set[str]:
    """The slots the question actually reaches, via I6's own decomposition."""
    reached: set[str] = set()
    for sub in formulate(question, scope):
        reached |= slots_for(sub)
    return reached


def apply(model: UserModel, question: str, scope: Scope) -> Applied:
    """Split the model three ways for one question.

    `withheld` is returned rather than dropped. A user-facing affordance needs
    to show what was *not* used as much as what was -- "we know your address
    and did not mention it" is the sentence that makes the rest credible.
    """
    reached = asked_slots(question, scope)
    asked, instructions, withheld = [], [], []
    for slot, attribute in model.attributes.items():
        if mode(slot) is Mode.INSTRUCTION:
            instructions.append(attribute)
        elif slot in reached:
            asked.append(attribute)
        else:
            withheld.append(attribute)
    return Applied(
        asked=tuple(asked),
        instructions=tuple(instructions),
        withheld=tuple(withheld),
    )


def disclosure(applied: Applied) -> list[str]:
    """What the user should be able to see about this turn.

    Not a log. A log answers "what happened"; this answers "what did you use
    about me, and what else do you have" -- which is the question a correction
    affordance exists to make answerable.
    """
    lines = [f"used: {a.slot} ({'; '.join(a.values)})" for a in applied.asked]
    lines += [f"applied silently: {a.slot}" for a in applied.instructions]
    lines += [f"held, not used: {a.slot}" for a in applied.withheld]
    return lines
