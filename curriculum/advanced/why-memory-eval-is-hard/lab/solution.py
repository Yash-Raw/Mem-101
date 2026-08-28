"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass

from memlab.fixtures import load_gold


@dataclass(frozen=True)
class Seam:
    """One thing `gold.yml` asserts, and whether it is machine-checkable."""

    name: str
    items: int
    checkable: bool
    why: str


def seams() -> list[Seam]:
    """What the answer key covers, and what a harness can actually score.

    `checkable` is the load-bearing column. A seam is checkable when its gold
    entry states a value a program can compare against the store. The rest are
    real and are prose -- a note explaining what to look for, which is a
    reviewer's instruction, not a test.
    """
    gold = load_gold()
    return [
        Seam("entities", len(gold["entities"]), True,
             "surface forms and a canonical id; comparable to `entities`"),
        Seam("supersessions", len(gold["supersessions"]), True,
             "subject, value and session; comparable to what is live"),
        Seam("relative_time", len(gold["relative_time"]), True,
             "phrase and the date it resolves to"),
        Seam("pii", len(gold["pii"]), True,
             "kind and value; comparable to the classifier's labels"),
        Seam("procedures", len(gold["procedures"]), True,
             "ordered steps and the critical one"),
        Seam("shared_memory", len(gold["shared_memory"]), True,
             "agent and trust level"),
        Seam("final_question", 1, True,
             "the exam: one question, one expected answer"),
        Seam("deletion_request", 1, False,
             "must_also_remove is five English sentences about structures"),
        Seam("persona", 1, False,
             "span and session count; describes the corpus, asserts nothing"),
    ]


def coverage(seams_: list[Seam]) -> tuple[int, int]:
    """(checkable seams, total seams)."""
    return sum(1 for s in seams_ if s.checkable), len(seams_)


def stages() -> tuple[str, ...]:
    """The write and read stages a wrong answer implicates, in order.

    Seven. The exam is a single boolean over all of them, which is why this
    course reached for module snapshots -- attributing a regression by
    bisecting the pipeline rather than by measuring any stage directly.
    """
    return (
        "extract",
        "resolve",
        "dedupe",
        "arbitrate",
        "decay",
        "rank",
        "assemble",
    )
