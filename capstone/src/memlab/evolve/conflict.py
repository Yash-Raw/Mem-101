"""Finding conflicting beliefs, and naming the relationship.

Two stages, and the first one is where the surprise is.

**Candidate generation cannot use similarity.** The obvious approach -- compare
beliefs that look alike -- fails on the exact case this course is built around:

    0.669  Priya is vegetarian            / Priya is pescatarian        refinement
    0.478  Priya drinks tea               / Priya works at Calico       PURE NOISE
    0.439  Priya does not drink coffee    / Priya drinks three coffees  contradiction
    0.285  Priya is a data engineer at    / Priya works at Calico       THE ONE
           Northwind Labs                                               THAT MATTERS

The employer contradiction scores **below noise**. Any threshold that surfaces
it surfaces everything. This is `embedding-recall`'s finding at its sharpest:
similarity measures shared wording, and two claims can contradict while sharing
almost none -- "data engineer at Northwind" and "works at Calico Systems"
disagree completely and overlap in one word.

So candidates are grouped by **slot** -- the attribute being claimed -- not by
appearance. Two beliefs conflict when they fill the same slot for the same
subject, whatever words they use.

**Naming the relationship** is the second stage, and it is a per-pair judgement:
contradiction, refinement, duplicate, or compatible. Per-pair matters for a
practical reason too -- the fake backend keys on the request, so a prompt that
embedded store state would invalidate every downstream fixture whenever an
upstream one changed.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from itertools import combinations

from ..llm.base import LLMClient, get_client
from ..types import Memory, MemoryType, Scope


class Relation(str, Enum):
    CONTRADICTION = "contradiction"   # both claim the slot; one must retire
    REFINEMENT = "refinement"         # the second narrows the first
    DUPLICATE = "duplicate"           # the same claim restated
    COMPATIBLE = "compatible"         # both can hold at once


# What attribute a claim fills. A production system has extraction emit this
# against a schema; a keyword map is the auditable version of the same idea,
# and it makes the grouping inspectable rather than magical.
SLOTS: dict[str, tuple[str, ...]] = {
    "employer": ("Northwind", "Calico", "data engineer", "staff engineer"),
    "diet": ("vegetarian", "pescatarian", "eat meat", "eats fish", "gluten"),
    "beverage": ("coffee", "tea"),
    "response_style": ("detailed explanations", "shorter answers"),
    "commute": ("cycle", "train", "commute"),
    "residence": ("lives at", "relocating", "moved"),
    "occupation_other": ("nurse", "works nights", "night"),
}

SCHEMA = {
    "type": "object",
    "properties": {"relation": {"enum": [r.value for r in Relation]}},
    "required": ["relation"],
}

PROMPT = (
    "Two beliefs about the same subject and attribute. Classify their relationship. "
    "contradiction: both claim the attribute now and cannot both be true. "
    "refinement: the second narrows or qualifies the first without negating it. "
    "duplicate: the same claim restated. "
    "compatible: both can hold at once. "
    'Reply with JSON: {"relation": "..."}'
)


@dataclass
class Conflict:
    a: Memory
    b: Memory
    slot: str
    relation: Relation


def slot_of(memory: Memory) -> str | None:
    for slot, markers in SLOTS.items():
        if any(m in memory.content for m in markers):
            return slot
    return None


def subject_of(memory: Memory, scope: Scope) -> frozenset[str]:
    return frozenset(memory.entities) or frozenset({scope.user})


def build_messages(a: str, b: str) -> list[dict]:
    """Keyed on the pair alone -- never on store state, so fixtures stay stable."""
    return [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": f"A: {a}\nB: {b}"},
    ]


def classify(a: Memory, b: Memory, client: LLMClient | None = None) -> Relation:
    client = client or get_client()
    raw = client.complete(build_messages(a.content, b.content), SCHEMA)
    payload = json.loads(raw) if isinstance(raw, str) else raw
    return Relation(payload["relation"])


def candidates(memories: list[Memory], scope: Scope) -> list[tuple[Memory, Memory, str]]:
    """Same subject, same slot. No similarity anywhere in this function."""
    beliefs = [m for m in memories if m.type is MemoryType.SEMANTIC and m.is_live]
    out = []
    for a, b in combinations(beliefs, 2):
        slot = slot_of(a)
        if slot is None or slot != slot_of(b):
            continue
        if subject_of(a, scope) != subject_of(b, scope):
            continue
        out.append((a, b, slot))
    return out


def detect(
    memories: list[Memory], scope: Scope, client: LLMClient | None = None
) -> list[Conflict]:
    client = client or get_client()
    return [
        Conflict(a=a, b=b, slot=slot, relation=classify(a, b, client))
        for a, b, slot in candidates(memories, scope)
    ]
