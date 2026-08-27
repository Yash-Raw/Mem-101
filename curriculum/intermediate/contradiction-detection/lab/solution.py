"""Reference solution."""
from __future__ import annotations

import json
from itertools import combinations

from memlab.evolve.conflict import SCHEMA, SLOTS, Relation, build_messages
from memlab.llm.base import LLMClient, get_client
from memlab.llm.fake import cosine, embed_text
from memlab.types import Memory, MemoryType, Scope

# Pairs whose true relationship we know, for scoring the two generators.
KNOWN = [
    ("Priya is vegetarian", "Priya is pescatarian", "refinement"),
    ("Priya drinks tea", "Priya works at Calico Systems", "NOISE"),
    ("Priya prefers detailed explanations with reasoning",
     "Priya prefers shorter answers", "contradiction"),
    ("Priya does not drink coffee", "Priya drinks three coffees a day", "contradiction"),
    ("Priya is a data engineer at Northwind Labs",
     "Priya works at Calico Systems", "contradiction"),
]


def slot_of(memory: Memory) -> str | None:
    for slot, markers in SLOTS.items():
        if any(m in memory.content for m in markers):
            return slot
    return None


def subject_of(memory: Memory, scope: Scope) -> frozenset[str]:
    return frozenset(memory.entities) or frozenset({scope.user})


def candidates(memories: list[Memory], scope: Scope) -> list[tuple[Memory, Memory, str]]:
    """Same subject, same slot. No similarity anywhere."""
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


def classify(a: Memory, b: Memory, client: LLMClient | None = None) -> Relation:
    client = client or get_client()
    raw = client.complete(build_messages(a.content, b.content), SCHEMA)
    payload = json.loads(raw) if isinstance(raw, str) else raw
    return Relation(payload["relation"])


def known_similarities() -> list[tuple[float, str, str, str]]:
    scored = [
        (cosine(embed_text(a), embed_text(b)), a, b, label) for a, b, label in KNOWN
    ]
    return sorted(scored, reverse=True, key=lambda t: t[0])


def similarity_candidates(
    memories: list[Memory], scope: Scope, threshold: float
) -> list[tuple[Memory, Memory]]:
    """The generator this lesson rejects, for measuring what it would cost."""
    beliefs = [m for m in memories if m.type is MemoryType.SEMANTIC and m.is_live]
    vectors = {m.id: embed_text(m.content) for m in beliefs}
    return [
        (a, b) for a, b in combinations(beliefs, 2)
        if subject_of(a, scope) == subject_of(b, scope)
        and cosine(vectors[a.id], vectors[b.id]) >= threshold
    ]
