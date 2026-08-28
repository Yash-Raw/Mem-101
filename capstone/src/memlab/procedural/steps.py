"""A procedure is a sequence, and the sequence is the content.

`extract/atomise.py` already refuses to split procedural memories, and that
refusal is why the order survives the write path at all -- four steps in one
record, in the order the user gave them:

    Priya's weekly report process: pull pipeline metrics from the warehouse,
    diff against last week, flag anything over 15% drift, write it up in the
    shared doc, in that order

What does not survive is the *link*. The user said two things in session 6:
the procedure, and "the diff step matters most". They are stored as two
memories with nothing connecting them, so the annotation can be retrieved
without the recipe -- which is exactly what `retrieving-procedures` measures.

So a procedure needs a representation, not just a string. Parsing one back out
of prose is possible here and it is a recovery, not a design: the structure
was thrown away at write time and is being reconstructed on read.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..types import Memory, MemoryType

_LEAD = re.compile(r"^.*?process:\s*", re.IGNORECASE)
_TRAIL = re.compile(r",?\s*in that order\.?\s*$", re.IGNORECASE)
_CRITICAL = re.compile(r"the (.+?) step matters most", re.IGNORECASE)


@dataclass(frozen=True)
class Procedure:
    """An ordered workflow, and the annotation about it if one was found."""

    memory: Memory
    steps: tuple[str, ...]
    critical: str | None = None

    @property
    def linked(self) -> bool:
        """Did the annotation find its way to the procedure?"""
        return self.critical is not None

    def position(self, step: str) -> int | None:
        for i, s in enumerate(self.steps, 1):
            if step in s:
                return i
        return None


def parse(memory: Memory) -> tuple[str, ...]:
    """Recover the ordered steps from the stored prose.

    Splitting on commas is fragile and it is the honest tool for the job: the
    write path stored a sentence, so a sentence is what there is to work with.
    A procedure captured as a list at extraction time would need none of this.
    """
    body = _TRAIL.sub("", _LEAD.sub("", memory.content))
    return tuple(s.strip() for s in body.split(",") if s.strip())


def annotation(memories: list[Memory]) -> tuple[Memory, str] | None:
    """A memory that says which step matters, if one was stored."""
    for m in memories:
        found = _CRITICAL.search(m.content)
        if found:
            return m, found.group(1).strip()
    return None


def build(memories: list[Memory]) -> list[Procedure]:
    """Every procedure in the store, with its annotation attached if findable.

    Attachment is by content, because there is no link to follow. `derived_from`
    would carry it and nothing populates it for annotations -- the two memories
    came from adjacent turns and the extractor treated them independently.
    """
    found = annotation(memories)
    out = []
    for m in memories:
        if m.type is not MemoryType.PROCEDURAL:
            continue
        # The annotation is *also* typed PROCEDURAL -- it is a comment about
        # a workflow, and the extractor had no way to say so. Splitting it on
        # commas yields a plausible two-step procedure that does not exist,
        # which is worse than dropping it, because it looks like data.
        if found and m.id == found[0].id:
            continue
        steps = parse(m)
        if len(steps) < 2:
            continue
        critical = None
        if found and found[0].id != m.id:
            critical = found[1]
        out.append(Procedure(memory=m, steps=steps, critical=critical))
    return out


def order_preserved(procedure: Procedure, expected: list[str]) -> bool:
    """Do the expected steps appear, in the expected order?"""
    positions = [procedure.position(step) for step in expected]
    return None not in positions and positions == sorted(positions)
