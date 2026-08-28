"""Why a memory system cannot be evaluated the way a retrieval system is.

Three structural problems, and this course has been living with all of them.

**There is no labelled corpus.** A retrieval benchmark ships queries and
relevance judgements over documents someone else wrote. Here the corpus is a
conversation, the "documents" are memories the system *created*, and the
labels are claims about what should have been extracted -- which is a judgement
about the system's own output. `gold.yml` is that judgement, written by hand,
and it covers nine seams.

**Ground truth moves.** *"Where does Priya work?"* has two correct answers
depending on when you ask, and both are in the transcript. A benchmark with one
answer key per question is asserting that memory does not change, which is the
one thing it certainly does.

**The write path is unlabelled.** The exam scores an *answer*. Between the turn
and the answer are extraction, resolution, dedupe, arbitration, decay, ranking
and packing, and a wrong answer implicates all seven. This course has spent
three levels working out which -- by building snapshots, not by measuring.

So the honest first deliverable is not a score. It is a count of what can be
scored at all.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..fixtures import load_gold


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
