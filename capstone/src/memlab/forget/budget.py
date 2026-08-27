"""A bounded store, and what "evict" is allowed to mean.

The whole course rests on supersede-never-destroy, and forgetting does not get
an exception. A memory that has faded is not false -- nobody contradicted it,
it simply stopped earning its place. Deleting it would throw away the only
copy of something still true.

So eviction here is **tier demotion plus exclusion from default retrieval**.
The record stays in the log, reachable by an explicit historical query, and
recoverable if it turns out to matter again. Physical removal is a governance
operation with a different trigger, and it lands in Advanced.

The cap is on the LONG_TERM tier rather than on the store, because that is what
actually costs: long-term memories are what default retrieval scans and what
competes for the token budget.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from ..types import Memory, Tier

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
