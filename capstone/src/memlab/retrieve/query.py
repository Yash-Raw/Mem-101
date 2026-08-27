"""The query is not the user's last message.

Three transformations, each fixing a failure the ranker cannot reach:

    resolve      "where do I work" is a question about Priya. Until the
                 pronoun is resolved, no term in the query names her, and
                 memories about her partner compete on equal footing.

    decompose    "where do I work AND what should I not eat" is two questions.
                 One embedding of both matches everything mediocrely -- the
                 employer sits at rank 2 for the compound form and rank 1 for
                 its own half.

    slots        "what should I not eat" and "Priya has a gluten intolerance"
                 share no vocabulary at all. Coverage is 0 and similarity is
                 weak, so a fact the question directly asks about ranks 10th.
                 The slot vocabulary from `contradiction-detection` already
                 knows that gluten is a diet fact; the read path can use the
                 same table the write path did.

Rules on the read path, deliberately. Extraction gets the one model call per
turn; retrieval runs on every query and must stay cheap.
"""
from __future__ import annotations

import re

from ..evolve.conflict import SLOTS
from ..types import Memory, Scope

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
    """Split a compound question. One question per retrieval."""
    parts = [p.strip(" ?.") for p in CONJUNCTION.split(query) if p.strip(" ?.")]
    return [f"{p}?" for p in parts] if len(parts) > 1 else [query]


def slots_for(query: str) -> set[str]:
    """Which attributes is this question about?"""
    lowered = query.lower()
    return {slot for slot, cues in SLOT_CUES.items() if any(c in lowered for c in cues)}


def in_slots(memories: list[Memory], slots: set[str]) -> list[Memory]:
    """Every live memory filling one of these attributes.

    Set membership, not similarity -- which is why it finds the gluten fact
    that shares no words with the question asking about it.
    """
    if not slots:
        return []
    markers = {m for slot in slots for m in SLOTS.get(slot, ())}
    return [m for m in memories if m.is_live and any(k in m.content for k in markers)]


def formulate(query: str, scope: Scope) -> list[str]:
    """The read-path rewrite: resolve, then split."""
    return decompose(resolve(query, scope))
