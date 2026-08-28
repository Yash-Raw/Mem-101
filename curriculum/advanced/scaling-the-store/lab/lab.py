"""Lab: replicate the store and watch which cost moves.

    uv run python curriculum/advanced/scaling-the-store/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.types import Memory


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
    raise NotImplementedError("implement replicate")


def measure(memories: list[Memory], scope, factor: int) -> Growth:
    """Store size, eligible pool and candidate pairs at a replication factor."""

    raise NotImplementedError("implement measure")


def partition_key() -> str:
    """What a real store shards on, and why it was not a scaling decision."""
    raise NotImplementedError("implement partition_key")


FACTORS = (1, 2, 4, 8)


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-scale.jsonl")
    store.clear()
    ingest(store, scope, at("A3"))
    memories = store.all()

    print(f"   {'x':>3}{'memories':>10}{'eligible':>10}{'pairs':>8}{'pairs/mem':>11}")
    for factor in FACTORS:
        growth = measure(memories, scope, factor)
        print(f"   {growth.factor:>3}{growth.memories:>10}{growth.eligible:>10}"
              f"{growth.pairs:>8}{growth.per_memory_pairs:>11}")

    first, last = measure(memories, scope, 1), measure(memories, scope, 8)
    print(f"\n   8x the store: {last.memories // first.memories}x the memories, "
          f"{last.eligible // first.eligible}x the pool, "
          f"{last.pairs // first.pairs}x the pairs")
    print(f"   partition key: {partition_key()}")


if __name__ == "__main__":
    main()
