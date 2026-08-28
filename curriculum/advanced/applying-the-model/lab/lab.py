"""Lab: apply the model, and be able to say what you held back.

    uv run python curriculum/advanced/applying-the-model/lab/lab.py
"""

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
    raise NotImplementedError("implement apply")


def disclosure(applied: Applied) -> list[str]:
    """What the user should be able to see about this turn.

    Not a log. A log answers "what happened"; this answers "what did you use
    about me, and what else do you have" -- which is the question a correction
    affordance exists to make answerable.
    """
    raise NotImplementedError("implement disclosure")


QUESTIONS = [
    "where do I work and what should I not eat?",
    "what should I not eat?",
    "where do I work?",
    "what am I like to talk to?",
]


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.assemble.simple import estimate_tokens
    from memlab.assemble.value import COMPACT_HEADER
    from memlab.eval.exam import exam_from_context
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.user.model import build

    scope = Scope(user="priya")
    pipeline = at("A3")
    store = JsonlStore("/tmp/memlab-apply.jsonl")
    store.clear()
    ingest(store, scope, pipeline)
    memories = store.all()
    model = build(memories, scope)

    everything = " ".join(
        v for a in model.attributes.values() for v in a.values
    )
    print(f"   {'question':44}{'asked':>6}{'silent':>8}{'held':>6}"
          f"{'tokens':>8}{'all six':>9}")
    for question in QUESTIONS:
        applied = apply(model, question, scope)
        used = " ".join(
            v for a in applied.asked + applied.instructions for v in a.values
        )
        print(f"   {question:44}{len(applied.asked):>6}"
              f"{len(applied.instructions):>8}{len(applied.withheld):>6}"
              f"{estimate_tokens(used):>8}{estimate_tokens(everything):>9}")

    applied = apply(model, QUESTIONS[0], scope)
    beliefs = [m for a in applied.asked for m in a.beliefs]
    context = COMPACT_HEADER + "\n" + "\n".join(f"- {m.content}" for m in beliefs)
    lowest = next(
        b for b in range(30, 90)
        if exam_from_context(memories, scope, k=5, pipeline=pipeline,
                             budget=b).is_correct
    )
    print(f"\n   model-driven context, with the compact header   "
          f"{estimate_tokens(context)} tokens, {len(beliefs)} memories")
    print(f"   retrieval path, lowest passing budget           {lowest}")

    print("\n   disclosure for the exam question:")
    for line in disclosure(applied):
        print(f"      {line[:72]}")


if __name__ == "__main__":
    main()
