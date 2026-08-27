"""Lab: what decays is relevance, not truth.

    uv run python curriculum/intermediate/decay-and-tiers/lab/lab.py
"""

from __future__ import annotations

import math
from dataclasses import replace
from datetime import datetime, timedelta

from memlab.types import Memory, MemoryType, Tier

HALF_LIFE = timedelta(days=180)

# How fast relevance falls, per type. An episode is over; a belief is current
# until superseded; a taught procedure is meant to outlast both.
DECAY_RATE = {
    MemoryType.EPISODIC: 1.0,
    MemoryType.WORKING: 1.0,
    MemoryType.SEMANTIC: 0.25,
    MemoryType.PROCEDURAL: 0.10,
}

# Tier thresholds. Deliberately wide bands: a memory should not oscillate
# across a boundary because its salience moved by a hundredth.
LONG_TERM_AT = 0.40
WORKING_AT = 0.20


def reference_now(memories: list[Memory]) -> datetime:
    """The newest event in the store. Deterministic by construction."""
    return max((m.happened_at or m.recorded_at) for m in memories)


def decayed(memory: Memory, now: datetime) -> float:
    """TODO: salience after age, scaled by DECAY_RATE for this memory's type.

    Each recorded use buys back one half-life. `uniform_apply` below is the
    version without the type scaling -- run both and compare.
    """
    raise NotImplementedError("implement decayed")


def tier_for(salience: float) -> Tier:
    if salience >= LONG_TERM_AT:
        return Tier.LONG_TERM
    if salience >= WORKING_AT:
        return Tier.WORKING
    return Tier.SCRATCH


def apply(memories: list[Memory], now: datetime | None = None) -> list[Memory]:
    """Age every memory and re-tier it. Nothing is removed."""
    if not memories:
        return []
    now = now or reference_now(memories)
    out = []
    for m in memories:
        value = decayed(m, now)
        out.append(replace(m, salience=value, tier=tier_for(value)))
    return out


def uniform_apply(memories: list[Memory], now: datetime | None = None) -> list[Memory]:
    """The first version: one half-life for everything. Empties the store."""
    if not memories:
        return []
    now = now or reference_now(memories)
    out = []
    for m in memories:
        age = now - (m.happened_at or m.recorded_at)
        effective = max(0.0, (age / HALF_LIFE) - m.access_count)
        value = round(m.salience * math.pow(0.5, effective), 3)
        out.append(replace(m, salience=value, tier=tier_for(value)))
    return out


def main() -> None:
    from collections import Counter

    from memlab.app.chat import ingest
    from memlab.forget import budget
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-decay.jsonl")
    store.clear()
    ingest(store, scope, at("I4"))
    from memlab.fixtures import load_turns
    from memlab.forget.salience import apply as score_salience

    turns = {f"s{t['session']}:{t['ts']}": t["text"] for t in load_turns(user_only=True)}
    scored = score_salience(store.all(), turns)

    naive = uniform_apply(scored)
    print("one half-life for everything:")
    print(f"  tiers: {dict(Counter(m.tier.value for m in naive if m.is_live))}")
    print(f"  retrievable: {len(budget.retrievable(naive))}   <- the store emptied\n")

    typed = apply(scored)
    print("scaled by type:")
    print(f"  tiers: {dict(Counter(m.tier.value for m in typed if m.is_live))}")
    print(f"  retrievable: {len(budget.retrievable(typed))}   store: {len(typed)} (unchanged)\n")

    print("what fell out of retrieval:")
    for m in sorted((m for m in typed if m.is_live and m.tier is not Tier.LONG_TERM),
                    key=lambda m: m.salience)[:6]:
        print(f"  {m.salience:.3f}  {m.type.value:<10} {m.content[:48]}")
    print("\nAll episodes. Every standing belief stayed.")


if __name__ == "__main__":
    main()
