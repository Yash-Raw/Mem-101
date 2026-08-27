"""Finding the names in a memory, before deciding who they refer to.

Beginner's store holds four ways of saying one person -- "Sam", "Samira",
"Sammy", "my partner" -- plus a bare "She" with no antecedent at all. Nothing
connects them, so evidence about one person sits in four records that never
meet: no contradiction between them is detectable, and nothing accumulates.

This module only *finds mentions*. Deciding which ones denote the same person
is resolution, and it is a separate job with a separate failure mode.
"""
from __future__ import annotations

import re

# Capitalised tokens that are not sentence-initial noise. Deliberately blunt --
# precision comes from the resolution step, not from here.
PROPER = re.compile(r"\b([A-Z][a-z]{2,})\b")

# Relationship terms that denote a person without naming one.
DESCRIPTORS = ("my partner", "her partner", "his partner", "my wife", "my husband")

PRONOUNS = ("she", "he", "they", "her", "him", "them")

# Capitalised tokens in this corpus that are not people. Grouped because this
# list is maintained by running the extractor and reading what comes out --
# every entry below was added after seeing it appear as a "person".
NOT_PEOPLE = frozenset(
    # the user, and organisations
    ["Priya", "Northwind", "Calico", "Labs", "Systems", "Spark"]
    # places
    + ["Bristol", "Halloway", "Road", "Aubyn", "Berlin"]
    # dates -- agent writes are full of these
    + ["January", "February", "March", "April", "June", "July", "August",
       "September", "October", "November", "December"]
    + ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    # sentence-openers and common nouns that happen to be capitalised
    + ["Morning", "Tea", "Very", "Also", "Quick", "Before", "Actually", "Still",
       "Reach", "Charge", "Nurse", "Debugging", "Pull", "Here", "The",
       "She", "He", "They"]
)


def proper_names(text: str) -> list[str]:
    return [n for n in PROPER.findall(text) if n not in NOT_PEOPLE]


def descriptors(text: str) -> list[str]:
    lowered = text.lower()
    return [d for d in DESCRIPTORS if d in lowered]


def leading_pronoun(text: str) -> str | None:
    """A memory that opens with a pronoun has no antecedent of its own."""
    first = text.split()[0].lower().strip(".,") if text.split() else ""
    return first if first in PRONOUNS else None


def mentions(text: str) -> list[str]:
    """Every surface form in this text that could denote a person."""
    found = proper_names(text) + descriptors(text)
    if (p := leading_pronoun(text)) and not found:
        found.append(p)
    return found
