"""Lab: recover the half of the sentence extraction threw away.

    uv run python curriculum/advanced/learning-from-outcomes/lab/lab.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from memlab.types import Memory

# "If you skip it, X" / "if you don't do Y, X". Conditionals are how people
# state consequences, and a consequence with no condition is just a fact.
_CONSEQUENCE = re.compile(
    r"\bif you (?:skip|miss|forget|don'?t)\s*(?P<what>[\w\s]*?)[,.]?\s+"
    r"(?P<then>[^.]+)\.?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Lesson:
    """A consequence the user stated, and the step it warns about."""

    trigger: str        # what you must not do
    consequence: str    # what happens if you do
    step: str | None = None
    source_id: str = ""

    @property
    def attached(self) -> bool:
        return self.step is not None


def extract(text: str, source_id: str = "") -> list[Lesson]:
    """Conditional consequences stated in a turn.

    Runs over the *transcript*, not the store, because the store no longer
    contains them. That is the point of the lesson and not a convenience:
    once the write path drops a clause, no amount of reading the store gets
    it back.
    """
    raise NotImplementedError("implement extract")


def attach(lesson: Lesson, steps: tuple[str, ...], critical: str | None) -> Lesson:
    """Bind a lesson to the step it warns about.

    The pronoun does the damage. "If you skip **it**" refers to whatever the
    previous sentence named, which is in a different sentence and, after
    extraction, a different memory. Resolving it needs the annotation, so the
    binding is only possible while both halves are still in hand.
    """
    raise NotImplementedError("implement attach")


def recorded(memories: list[Memory], lesson: Lesson) -> bool:
    """Is this consequence anywhere in the store?"""
    raise NotImplementedError("implement recorded")


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.fixtures import load_turns
    from memlab.pipeline import at
    from memlab.procedural.steps import build
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-outcomes.jsonl")
    store.clear()
    ingest(store, scope, at("A3"))
    memories = store.all()
    procedure = build(memories)[0]

    lessons = []
    for turn in load_turns():
        if turn["session"] < 14:
            lessons += extract(turn["text"], f"s{turn['session']}:{turn['ts']}")

    print(f"lessons stated in the corpus: {len(lessons)}\n")
    for lesson in lessons:
        bound = attach(lesson, procedure.steps, procedure.critical)
        print(f"   trigger     : {bound.trigger!r}")
        print(f"   consequence : {bound.consequence!r}")
        print(f"   step        : {bound.step!r}  (attached={bound.attached})")
        print(f"   in the store: {recorded(memories, bound)}")

    from_store = []
    for memory in memories:
        from_store += extract(memory.content, memory.provenance.source_id)
    print(f"\n   the same extractor run over the store: {len(from_store)} lessons")


if __name__ == "__main__":
    main()
