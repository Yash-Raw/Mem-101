"""Lab: a procedure is a sequence, and one of these is not a procedure.

    uv run python curriculum/advanced/procedural-memory/lab/lab.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from memlab.types import Memory, MemoryType

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
    raise NotImplementedError("implement parse")


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
    raise NotImplementedError("implement build")


def order_preserved(procedure: Procedure, expected: list[str]) -> bool:
    """Do the expected steps appear, in the expected order?"""
    raise NotImplementedError("implement order_preserved")


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.fixtures import load_gold
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-procedural.jsonl")
    store.clear()
    ingest(store, scope, at("A3"))
    memories = store.all()
    gold = load_gold()["procedures"][0]

    typed = sum(1 for m in memories if m.type is MemoryType.PROCEDURAL)
    procedures = build(memories)
    print(f"procedural memories in the store   {typed}")
    print(f"procedures recovered              {len(procedures)}\n")

    procedure = procedures[0]
    for i, step in enumerate(procedure.steps, 1):
        print(f"   {i}. {step}")
    print(f"\n   order matches gold: "
          f"{order_preserved(procedure, gold['ordered_steps'])}")
    print(f"   critical step     : {procedure.critical!r} at position "
          f"{procedure.position(procedure.critical)} of {len(procedure.steps)}")

    found = annotation(memories)
    print("\n   the annotation lives in its own memory:")
    print(f"      {found[0].content!r}")
    print(f"      derived_from: {found[0].derived_from}  -- nothing links the two")
    print(f"\n   what the annotation would have become: {list(parse(found[0]))}")


if __name__ == "__main__":
    main()
