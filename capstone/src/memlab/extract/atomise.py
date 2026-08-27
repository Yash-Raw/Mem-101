"""One fact per record -- and knowing when that rule is wrong.

Atomicity exists to keep memories *updatable*: you cannot mark half a record
superseded, so a compound memory has to be deleted and rewritten wholesale,
losing its history.

Procedures are the deliberate exception. Their order is load-bearing, and
splitting a workflow into atomic steps produces records that are individually
retrievable and collectively useless. When the two principles collide,
updatability yields to usability.
"""
from __future__ import annotations

import re

from ..types import MemoryType

# Conjunctions that usually join two independent claims. Deliberately narrow:
# over-splitting is as damaging as under-splitting, and a wrong split cannot be
# detected downstream.
SPLIT = re.compile(r",\s+and\s+(?=(?:she|he|they|priya)\b)", re.IGNORECASE)


def atomise(content: str, memory_type: MemoryType) -> list[str]:
    """Split a compound claim, unless splitting would destroy it."""
    if memory_type is MemoryType.PROCEDURAL:
        return [content]
    parts = [p.strip() for p in SPLIT.split(content) if p.strip()]
    return parts if len(parts) > 1 else [content]


def is_atomic(content: str, memory_type: MemoryType) -> bool:
    return len(atomise(content, memory_type)) == 1
