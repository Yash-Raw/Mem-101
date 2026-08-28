"""Lab: stop asking a workflow to compete with facts.

    uv run python curriculum/advanced/retrieving-procedures/lab/lab.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from memlab.procedural.steps import Procedure
from memlab.types import Memory, MemoryType

# A procedural request asks how to act, not what is true. Narrow on purpose:
# "what did I say about the Spark job" is a recall question that mentions work.
_HOW = re.compile(
    r"\bhow do i\b|\bhow to\b|\bwhat are the steps\b|\bwalk me through\b|"
    r"\bremind me how\b|\bwhat.s the process\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ProceduralHit:
    """A whole workflow, not a ranked fragment."""

    procedure: Procedure
    matched: int          # how many of the question's words the steps cover

    @property
    def steps(self) -> tuple[str, ...]:
        return self.procedure.steps


def is_procedural(question: str) -> bool:
    """Does this question ask how to do something?"""
    raise NotImplementedError("implement is_procedural")


def _words(text: str) -> set[str]:
    return {w.strip("?.,'").lower() for w in text.split() if len(w.strip("?.,'")) > 3}


def search(question: str, memories: list[Memory], limit: int = 1) -> list[ProceduralHit]:
    """Look only at procedures, and score over the whole workflow.

    The index is the difference. Scoring a procedure against the same pool as
    facts is what buries it: it is one long memory competing with short ones
    on a metric that rewards brevity. Restricted to procedures, length stops
    being a penalty and the annotation is not a candidate at all.
    """
    raise NotImplementedError("implement search")


def render(hit: ProceduralHit) -> str:
    """Inject the workflow whole, numbered, with the warning attached.

    Numbered because the order is the content, and a packer that drops the
    fourth step to save four tokens has produced a procedure that is wrong
    rather than short. `slot-value` measured dropping as the thing that makes
    a tight budget survivable; this is the memory type where it is not
    allowed.
    """
    raise NotImplementedError("implement render")


def procedural_memories(memories: list[Memory]) -> list[Memory]:
    return [m for m in memories if m.type is MemoryType.PROCEDURAL]


QUESTIONS = [
    "how do I do the weekly report?",
    "what are the steps for the weekly report",
    "where do I work?",
    "what did I say about the Spark job?",
]


def main() -> None:
    from memlab.app.chat import ask, ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    pipeline = at("A3")
    store = JsonlStore("/tmp/memlab-procretrieve.jsonl")
    store.clear()
    ingest(store, scope, pipeline)
    pipeline.vectors.index(store.all())
    memories = store.all()

    print(f"   {'question':44}{'procedural?':>13}{'fact-path rank':>16}"
          f"{'procedural path':>17}")
    for question in QUESTIONS:
        hits = ask(store, scope, question, k=5, pipeline=pipeline)[1]
        rank = next(
            (i + 1 for i, h in enumerate(hits)
             if h.memory.type is MemoryType.PROCEDURAL),
            None,
        )
        found = search(question, memories)
        print(f"   {question:44}{is_procedural(question)!s:>13}"
              f"{rank!s:>16}{('1 workflow' if found else '-'):>17}")

    hits = ask(store, scope, QUESTIONS[1], k=5, pipeline=pipeline)[1]
    print("\n   what the fact path returns at rank 1:")
    print(f"      {hits[0].memory.content}")

    print("\n   what the procedural path returns:\n")
    for line in render(search(QUESTIONS[0], memories)[0]).splitlines():
        print(f"      {line}")


if __name__ == "__main__":
    main()
