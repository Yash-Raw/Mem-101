"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass, replace

from memlab.types import Memory, Tier

DEFAULT_CAP = 20


@dataclass
class Eviction:
    memory: Memory
    from_tier: Tier
    to_tier: Tier
    reason: str


def enforce(
    memories: list[Memory], cap: int = DEFAULT_CAP
) -> tuple[list[Memory], list[Eviction]]:
    """Keep the `cap` most salient live memories in LONG_TERM. Demote the rest."""
    live_long = [m for m in memories if m.is_live and m.tier is Tier.LONG_TERM]
    if len(live_long) <= cap:
        return list(memories), []

    keep = {
        m.id for m in sorted(live_long, key=lambda m: (-m.salience, m.id))[:cap]
    }
    evictions = [
        Eviction(m, Tier.LONG_TERM, Tier.WORKING, f"below the top {cap} by salience")
        for m in live_long
        if m.id not in keep
    ]
    demoted = {e.memory.id for e in evictions}

    out = [replace(m, tier=Tier.WORKING) if m.id in demoted else m for m in memories]
    return out, evictions


def retrievable(memories: list[Memory]) -> list[Memory]:
    """What default retrieval sees: live, and not demoted out of the way."""
    return [m for m in memories if m.is_live and m.tier is Tier.LONG_TERM]


def cap_sweep(memories: list[Memory], caps=(20, 16, 12, 8)) -> list[tuple]:
    """(cap, retrievable, store size, exam correct, first casualty)."""
    from memlab.eval.exam import exam_answer
    from memlab.types import Scope

    scope = Scope(user="priya")
    baseline = {m.id for m in retrievable(memories)}
    rows = []
    for cap in caps:
        capped, evictions = enforce(memories, cap=cap)
        kept = retrievable(capped)
        answer = exam_answer(kept, scope)
        lost = [e.memory.content for e in evictions if e.memory.id in baseline]
        rows.append((cap, len(kept), len(capped), answer.is_correct,
                     sorted(answer.avoid), lost))
    return rows
