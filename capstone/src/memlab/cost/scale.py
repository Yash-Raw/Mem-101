"""What grows with what, measured by replication rather than guessed.

`graph-stores` established the rule this module follows: measure the shape
before adopting the architecture. So instead of asserting that a store needs
partitioning, replicate the corpus and watch which costs move.

The three candidates, and what each is a function of:

    write cost      turns          -- extraction reads one turn
    read cost       eligible pool  -- ranking scores what the filters admit
    consolidation   store size     -- a pass over everything

Only the third grows with the store, which is why `sleep-time-compute` was a
scheduling lesson rather than a scaling one. And the partition key is not a
performance choice: `scopes.partition` already shards on user, because that is
where the correctness boundary is -- so the thing a real store shards on was
fixed two levels ago for a reason that had nothing to do with size.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from ..types import Memory


@dataclass(frozen=True)
class Growth:
    """How a cost behaves as the store is replicated."""

    factor: int
    memories: int
    eligible: int
    pairs: int

    @property
    def per_memory_pairs(self) -> float:
        return round(self.pairs / self.memories, 1) if self.memories else 0.0


def replicate(memories: list[Memory], factor: int) -> list[Memory]:
    """`factor` copies of the store, each with distinct ids.

    Content-addressed ids mean a naive copy deduplicates itself into the
    original -- which is the store working correctly and useless for a
    scaling measurement. The source id is varied so the copies are genuinely
    distinct records rather than the same record counted twice.
    """
    out = list(memories)
    for n in range(1, factor):
        for m in memories:
            out.append(
                replace(
                    m,
                    provenance=replace(
                        m.provenance, source_id=f"{m.provenance.source_id}#{n}"
                    ),
                    id="",
                )
            )
    return out


def measure(memories: list[Memory], scope, factor: int) -> Growth:
    """Store size, eligible pool and candidate pairs at a replication factor."""
    from ..evolve.conflict import candidates
    from ..retrieve.scoped import eligible

    grown = replicate(memories, factor)
    return Growth(
        factor=factor,
        memories=len(grown),
        eligible=len(eligible(grown, scope)),
        pairs=len(candidates(grown, scope)),
    )


def partition_key() -> str:
    """What a real store shards on, and why it was not a scaling decision."""
    return (
        "user -- fixed by scopes.partition as a correctness boundary, before "
        "size was a consideration"
    )
