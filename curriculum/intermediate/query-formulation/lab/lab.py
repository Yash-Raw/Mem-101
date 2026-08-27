"""Lab: three rewrites, and the one that reaches past vocabulary.

    uv run python curriculum/intermediate/query-formulation/lab/lab.py
"""

from __future__ import annotations

import re

from memlab.types import Memory, Scope

FIRST_PERSON = re.compile(r"\b(i|me|my|mine)\b", re.IGNORECASE)
CONJUNCTION = re.compile(r"\s+and\s+(?=what|where|when|who|how|why)", re.IGNORECASE)

# Which slot a question is asking about. The same vocabulary the write path
# uses to group conflicting beliefs -- one table, two consumers.
SLOT_CUES: dict[str, tuple[str, ...]] = {
    "diet": ("eat", "food", "diet", "allerg", "intoleran", "restrict"),
    "employer": ("work", "job", "employer", "company", "employed"),
    "beverage": ("drink", "coffee", "tea"),
    "response_style": ("answer", "explain", "detail", "brief"),
    "commute": ("commute", "travel", "get to work"),
    "residence": ("live", "address", "home"),
}


def resolve(query: str, scope: Scope) -> str:
    """First person refers to the account holder. Name them."""
    return FIRST_PERSON.sub(scope.user.capitalize(), query)


def decompose(query: str) -> list[str]:
    """TODO: split on CONJUNCTION, restore the question marks.

    Return the original unchanged if it does not split -- one question is not
    a degenerate compound.
    """
    raise NotImplementedError("implement decompose")


def slots_for(query: str) -> set[str]:
    """Which attributes is this question about?"""
    lowered = query.lower()
    return {slot for slot, cues in SLOT_CUES.items() if any(c in lowered for c in cues)}


def in_slots(memories: list[Memory], slots: set[str]) -> list[Memory]:
    """TODO: every live memory filling one of these attributes.

    Use the SLOTS table from contradiction-detection. Set membership, not
    similarity -- that is what reaches the gluten fact.
    """
    raise NotImplementedError("implement in_slots")


def formulate(query: str, scope: Scope) -> list[str]:
    """The read-path rewrite: resolve, then split."""
    return decompose(resolve(query, scope))


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.eval.exam import QUESTION
    from memlab.pipeline import at
    from memlab.retrieve.scoped import eligible
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-query.jsonl")
    store.clear()
    ingest(store, scope, at("I5"))
    pool = eligible(store.all(), scope)

    print(f"raw:        {QUESTION!r}")
    print(f"resolved:   {resolve(QUESTION, scope)!r}")
    print(f"formulated: {formulate(QUESTION, scope)}\n")

    for sub in formulate(QUESTION, scope):
        found = in_slots(pool, slots_for(sub))
        print(f"  {sub!r} -> slots {slots_for(sub)}")
        for m in found:
            print(f"       {m.content[:54]}")
        print()

    gluten = next(m for m in pool if m.content == "Priya has a gluten intolerance")
    shared = set(gluten.content.lower().split()) & set(QUESTION.lower().split())
    print(f"words shared between the question and the gluten fact: {shared or 'none'}")
    print("Set membership found it. Similarity could not have.")


if __name__ == "__main__":
    main()
