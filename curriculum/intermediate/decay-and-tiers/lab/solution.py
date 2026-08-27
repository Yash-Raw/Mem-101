"""Reference solution."""

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
    """Salience after age, scaled by how fast this type loses relevance."""
    age = now - (memory.happened_at or memory.recorded_at)
    half_lives = (age / HALF_LIFE) * DECAY_RATE[memory.type]
    # Each recorded use buys back one half-life of age.
    effective = max(0.0, half_lives - memory.access_count)
    return round(memory.salience * math.pow(0.5, effective), 3)


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
