"""Lab: finding the names, before deciding who they are.

    uv run python curriculum/intermediate/entities-and-aliases/lab/lab.py
"""
from __future__ import annotations

import re

from memlab.entity.aliases import DESCRIPTORS, PRONOUNS

PROPER = re.compile(r"\b([A-Z][a-z]{2,})\b")


def proper_names(text: str) -> list[str]:
    """TODO: capitalised tokens that are not in NOT_PEOPLE."""
    raise NotImplementedError("implement proper_names")


def descriptors(text: str) -> list[str]:
    lowered = text.lower()
    return [d for d in DESCRIPTORS if d in lowered]


def leading_pronoun(text: str) -> str | None:
    """TODO: return the pronoun only if the text STARTS with one.

    A pronoun mid-sentence usually has its antecedent nearby. One at the very
    front is the case where extraction severed it.
    """
    raise NotImplementedError("implement leading_pronoun")


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


PARTNER = ("Sam ", "Sam's", "Samira", "Sammy", "partner")


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    store = JsonlStore("/tmp/memlab-aliases.jsonl")
    store.clear()
    ingest(store, Scope(user="priya"), at("I2"))

    about_partner = [
        m for m in store.all()
        if any(n in m.content for n in PARTNER) or m.content.startswith("She")
    ]
    print(f"{len(about_partner)} memories about one person:\n")
    for content, found, orphan in audit_mentions(about_partner):
        flag = "  <-- names NOBODY" if orphan else ""
        print(f"  {found!s:<26} {content[:46]}{flag}")

    orphans = [c for c, _, o in audit_mentions(store.all()) if o]
    print(f"\n{len(orphans)} memory in the whole store names nobody at all.")
    print("It is the one the next lesson has to work hardest for.")


if __name__ == "__main__":
    main()
