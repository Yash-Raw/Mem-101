"""Reference solution."""
from __future__ import annotations

from dataclasses import replace

from memlab.extract.gate import ACTIVITY, EXPLICIT
from memlab.forget.salience import (
    ACTIVITY_PENALTY,
    BASE,
    CORROBORATION_BONUS,
    EXPLICIT_BONUS,
    HEARSAY_PENALTY,
    PROCEDURE_BONUS,
    USE_BONUS,
)
from memlab.llm.fake import cosine, embed_text
from memlab.types import Memory, MemoryType


def score(memory: Memory, turn_text: str = "") -> float:
    value = BASE
    if any(marker in turn_text.lower() for marker in EXPLICIT):
        value += EXPLICIT_BONUS
    if memory.type is MemoryType.PROCEDURAL:
        value += PROCEDURE_BONUS
    value += CORROBORATION_BONUS * len(memory.derived_from)
    value += USE_BONUS * memory.access_count
    if any(marker in memory.content for marker in ACTIVITY):
        value -= ACTIVITY_PENALTY
    if memory.provenance.authority < 0.5:
        value -= HEARSAY_PENALTY
    return round(min(1.0, max(0.0, value)), 3)


def apply(memories: list[Memory], turns: dict[str, str] | None = None) -> list[Memory]:
    turns = turns or {}
    return [
        replace(m, salience=score(m, turns.get(m.provenance.source_id, "")))
        for m in memories
    ]


def record_use(memories: list[Memory], used_ids: set[str]) -> list[Memory]:
    return [
        replace(m, access_count=m.access_count + 1) if m.id in used_ids else m
        for m in memories
    ]


def rank_with_salience(
    query: str, memories: list[Memory], weight: float
) -> list[tuple[float, Memory]]:
    """The obvious use of the score. Measure it before believing in it."""
    q = embed_text(query)
    scored = [
        (cosine(q, embed_text(m.content)) + weight * m.salience, m)
        for m in memories if m.is_live
    ]
    scored.sort(key=lambda pair: -pair[0])
    return scored
