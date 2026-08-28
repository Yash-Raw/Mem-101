"""Reference solution."""

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
    return [
        Lesson(
            trigger=(m.group("what") or "it").strip() or "it",
            consequence=m.group("then").strip(),
            source_id=source_id,
        )
        for m in _CONSEQUENCE.finditer(text)
    ]


def attach(lesson: Lesson, steps: tuple[str, ...], critical: str | None) -> Lesson:
    """Bind a lesson to the step it warns about.

    The pronoun does the damage. "If you skip **it**" refers to whatever the
    previous sentence named, which is in a different sentence and, after
    extraction, a different memory. Resolving it needs the annotation, so the
    binding is only possible while both halves are still in hand.
    """
    if lesson.trigger.lower() not in ("it", "this", "that"):
        match = next((s for s in steps if lesson.trigger.lower() in s.lower()), None)
    else:
        match = next(
            (s for s in steps if critical and critical.lower() in s.lower()), None
        )
    return Lesson(
        trigger=lesson.trigger,
        consequence=lesson.consequence,
        step=match,
        source_id=lesson.source_id,
    )


def recorded(memories: list[Memory], lesson: Lesson) -> bool:
    """Is this consequence anywhere in the store?"""
    needle = lesson.consequence.lower()[:20]
    return any(needle in m.content.lower() for m in memories)
