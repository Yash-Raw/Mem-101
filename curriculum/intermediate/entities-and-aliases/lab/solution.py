"""Reference solution."""
from __future__ import annotations

import re

from memlab.entity.aliases import DESCRIPTORS, NOT_PEOPLE, PRONOUNS

PROPER = re.compile(r"\b([A-Z][a-z]{2,})\b")


def proper_names(text: str) -> list[str]:
    return [n for n in PROPER.findall(text) if n not in NOT_PEOPLE]


def descriptors(text: str) -> list[str]:
    lowered = text.lower()
    return [d for d in DESCRIPTORS if d in lowered]


def leading_pronoun(text: str) -> str | None:
    """Only a memory that OPENS with a pronoun has lost its antecedent."""
    first = text.split()[0].lower().strip(".,") if text.split() else ""
    return first if first in PRONOUNS else None


def mentions(text: str) -> list[str]:
    found = proper_names(text) + descriptors(text)
    if (p := leading_pronoun(text)) and not found:
        found.append(p)
    return found


def audit_mentions(memories) -> list[tuple[str, list[str], bool]]:
    """(content, mentions, is_orphaned) -- orphaned means pronoun-only."""
    out = []
    for m in memories:
        found = mentions(m.content)
        orphan = bool(found) and all(f in PRONOUNS for f in found)
        out.append((m.content, found, orphan))
    return out
