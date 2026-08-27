"""Reference solution."""
from __future__ import annotations

import re
from dataclasses import dataclass

from memlab.types import Memory, MemoryType

SPLIT = re.compile(r",\s+and\s+(?=(?:she|he|they|priya)\b)", re.IGNORECASE)


def atomise(content: str, memory_type: MemoryType) -> list[str]:
    """Split independent claims -- unless splitting destroys the memory."""
    if memory_type is MemoryType.PROCEDURAL:
        return [content]
    parts = [p.strip() for p in SPLIT.split(content) if p.strip()]
    return parts if len(parts) > 1 else [content]


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
