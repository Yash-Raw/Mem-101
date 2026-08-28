"""Storing less on purpose, and finding out what less costs.

`pii-on-the-write-path` measured that refusing personal data breaks the exam.
Redaction is the middle option: keep the fact, drop the detail.

Three levels, and the interesting one is the middle:

    FULL       Priya lives at 47 Halloway Road, Bristol
    COARSE     Priya lives in Bristol
    TOKENISED  Priya lives at <address>

`COARSE` is the one that has to be designed per kind, because "less precise"
means something different for a street address than for a phone number -- a
city is useful and half a phone number is not. `TOKENISED` is uniform and
keeps only that the fact exists, which is exactly what a deletion audit needs
and exactly what an answer cannot use.

The measurement that matters is not how much text was removed. It is whether
the exam still passes, per level, per kind -- because a redaction that costs
nothing is one nobody has a reason to argue about.
"""
from __future__ import annotations

import re
from dataclasses import replace
from enum import Enum

from ..types import Memory
from .classify import Kind, classify


class Level(str, Enum):
    FULL = "full"
    COARSE = "coarse"
    TOKENISED = "tokenised"


# Per-kind coarsening. Each entry throws away a different thing, because
# "less precise" is not one operation: a city is a useful address, and there
# is no useful half of a phone number.
_COARSE: dict[Kind, tuple[re.Pattern, str]] = {
    Kind.ADDRESS: (re.compile(r"lives at [\w\s]+?,\s*(\w+)", re.IGNORECASE), r"lives in \1"),
    Kind.PHONE: (re.compile(r"\b0\d{4}\s?\d{6}\b"), "on file"),
    # Drops the diagnosis *event* and keeps the condition: "was diagnosed
    # with X last week" carries a date and a clinical encounter that a
    # question about food does not need.
    Kind.HEALTH: (
        re.compile(r"\bwas diagnosed with an?\b", re.IGNORECASE),
        "has a",
    ),
}

_TOKEN = {
    Kind.ADDRESS: "<address>",
    Kind.PHONE: "<phone>",
    Kind.HEALTH: "<health condition>",
    Kind.THIRD_PARTY_HEALTH: "<third party>",
}


def redact(memory: Memory, level: Level) -> Memory:
    """Rewrite a memory's content at the given level of detail.

    Content-addressed ids change when content changes, which is correct and
    load-bearing: a redacted memory is a different record, and pretending
    otherwise would let a full-detail copy and a redacted one share an id.
    """
    kind = classify(memory)
    if kind is None or level is Level.FULL:
        return memory

    if level is Level.TOKENISED:
        return replace(memory, content=_token(memory, kind), id="")

    pattern = _COARSE.get(kind)
    if pattern is None:
        return replace(memory, content=_token(memory, kind), id="")
    return replace(memory, content=pattern[0].sub(pattern[1], memory.content), id="")


def _token(memory: Memory, kind: Kind) -> str:
    """Keep the subject and the shape; drop the value."""
    subject = memory.content.split()[0]
    return f"{subject} — {_TOKEN[kind]}"


def apply(memories: list[Memory], level: Level, kinds: set[Kind]) -> list[Memory]:
    """Redact the selected kinds; leave everything else alone."""
    return [
        redact(m, level) if classify(m) in kinds else m
        for m in memories
    ]
