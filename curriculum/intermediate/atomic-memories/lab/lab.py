"""Lab: the grain that stays updatable.

    uv run python curriculum/intermediate/atomic-memories/lab/lab.py
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from memlab.types import Memory, MemoryType

SPLIT = re.compile(r",\s+and\s+(?=(?:she|he|they|priya)\b)", re.IGNORECASE)


def atomise(content: str, memory_type: MemoryType) -> list[str]:
    """TODO: split on SPLIT, but return PROCEDURAL content untouched.

    Order is load-bearing in a procedure; splitting one produces steps that
    are individually retrievable and collectively useless.
    """
    raise NotImplementedError("implement atomise")


def is_atomic(content: str, memory_type: MemoryType) -> bool:
    return len(atomise(content, memory_type)) == 1


@dataclass
class AtomicityAudit:
    total: int
    compound: list[str]
    longest: tuple[int, str, str]

    @property
    def rate(self) -> float:
        return len(self.compound) / self.total if self.total else 0.0


def audit_atomicity(memories: list[Memory]) -> AtomicityAudit:
    compound = [m.content for m in memories if not is_atomic(m.content, m.type)]
    longest = max(memories, key=lambda m: len(m.content))
    return AtomicityAudit(
        total=len(memories),
        compound=compound,
        longest=(len(longest.content), longest.type.value, longest.content),
    )


CASES = [
    ("Priya eats fish, and she does not eat meat", MemoryType.SEMANTIC),
    ("Priya works at Calico Systems", MemoryType.SEMANTIC),
    ("Pull metrics, and diff against last week, and flag drift", MemoryType.PROCEDURAL),
]


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import get
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    store = JsonlStore("/tmp/memlab-atomic.jsonl")
    store.clear()
    ingest(store, Scope(user="priya"), get("intermediate"))

    audit = audit_atomicity(store.all())
    print(f"corpus: {len(audit.compound)} of {audit.total} non-atomic "
          f"({audit.rate:.0%})")
    n, kind, content = audit.longest
    print(f"longest record: {n} chars, {kind}")
    print(f"  {content[:72]}...")
    print(f"  splits into {len(atomise(content, MemoryType.PROCEDURAL))}\n")

    print("constructed cases:")
    for text, kind in CASES:
        parts = atomise(text, kind)
        print(f"  {kind.value:<11} -> {len(parts)}  {parts}")


if __name__ == "__main__":
    main()
