"""Reference solution."""

from __future__ import annotations

import re
from dataclasses import dataclass

from memlab.procedural.steps import Procedure, build
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
    return bool(_HOW.search(question))


def _words(text: str) -> set[str]:
    return {w.strip("?.,'").lower() for w in text.split() if len(w.strip("?.,'")) > 3}


def search(question: str, memories: list[Memory], limit: int = 1) -> list[ProceduralHit]:
    """Look only at procedures, and score over the whole workflow.

    The index is the difference. Scoring a procedure against the same pool as
    facts is what buries it: it is one long memory competing with short ones
    on a metric that rewards brevity. Restricted to procedures, length stops
    being a penalty and the annotation is not a candidate at all.
    """
    if not is_procedural(question):
        return []
    asked = _words(question)
    scored = []
    for procedure in build(memories):
        covered = asked & (_words(procedure.memory.content) | _words(
            " ".join(procedure.steps)
        ))
        if covered:
            scored.append(ProceduralHit(procedure=procedure, matched=len(covered)))
    scored.sort(key=lambda h: -h.matched)
    return scored[:limit]


def render(hit: ProceduralHit) -> str:
    """Inject the workflow whole, numbered, with the warning attached.

    Numbered because the order is the content, and a packer that drops the
    fourth step to save four tokens has produced a procedure that is wrong
    rather than short. `slot-value` measured dropping as the thing that makes
    a tight budget survivable; this is the memory type where it is not
    allowed.
    """
    lines = [f"{i}. {step}" for i, step in enumerate(hit.steps, 1)]
    if hit.procedure.critical:
        position = hit.procedure.position(hit.procedure.critical)
        lines.append(f"(step {position} matters most)")
    return "\n".join(lines)


def procedural_memories(memories: list[Memory]) -> list[Memory]:
    return [m for m in memories if m.type is MemoryType.PROCEDURAL]
