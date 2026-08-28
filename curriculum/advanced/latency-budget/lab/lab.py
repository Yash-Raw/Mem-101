"""Lab: split the write path by what a user can wait for.

    uv run python curriculum/advanced/latency-budget/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class When(str, Enum):
    SYNCHRONOUS = "synchronous"
    DEFERRED = "deferred"


@dataclass(frozen=True)
class Stage:
    name: str
    when: When
    why: str


def split() -> list[Stage]:
    """Which stages block the turn, and why each is where it is."""
    raise NotImplementedError("implement split")


@dataclass(frozen=True)
class Budget:
    """Model calls on the critical path, per turn."""

    synchronous: float
    deferred: float

    @property
    def total(self) -> float:
        return round(self.synchronous + self.deferred, 2)

    @property
    def blocking_share(self) -> float:
        return round(self.synchronous / self.total, 3) if self.total else 0.0


def budget(extract_calls: int, consolidation_calls: int, turns: int) -> Budget:
    """Per-turn split, counted by where each completion actually runs.

    The first version of this took `cost-model`'s total -- 48 -- as the
    extraction count and reported 81% blocking. Half of those 48 are
    `conflict.classify`, and measuring where they fire settles it: **0**
    during the per-turn loop and 24 during consolidation. Conflict detection
    is a model call and it is entirely deferred.
    """
    raise NotImplementedError("implement budget")


TURNS = 24


def main() -> None:
    import memlab.evolve.conflict as conflict_mod
    from memlab.app.chat import _agent_memories
    from memlab.fixtures import load_turns
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    stages = split()
    for stage in stages:
        print(f"   {stage.name:11}{stage.when.value:14}{stage.why[:58]}")

    synchronous = sum(1 for s in stages if s.when is When.SYNCHRONOUS)
    print(f"\n   synchronous stages: {synchronous} of {len(stages)}")

    # Where each completion actually fires. Counting them by stage is what
    # separates the two halves of cost-model's 48.
    scope = Scope(user="priya")
    pipeline = at("A3")
    store = JsonlStore("/tmp/memlab-latency.jsonl")
    store.clear()
    counts = {"extract": 0, "classify": 0}
    original = conflict_mod.classify
    conflict_mod.classify = lambda *a, **k: (
        counts.__setitem__("classify", counts["classify"] + 1),
        original(*a, **k),
    )[1]
    try:
        for turn in (t for t in load_turns(user_only=True) if t["session"] < 14):
            written = pipeline.extract(turn, scope)
            counts["extract"] += 1
            if pipeline.resolve is not None:
                written = pipeline.resolve(written, store.all())
            store.add(written)
        during_turns = counts["classify"]
        store.add(_agent_memories(scope))
        store.replace(pipeline.consolidate(store.all()))
    finally:
        conflict_mod.classify = original

    print(f"\n   classify calls during the per-turn loop : {during_turns}")
    print(f"   classify calls during consolidation     : "
          f"{counts['classify'] - during_turns}")

    per_turn = budget(counts["extract"], counts["classify"] - during_turns, TURNS)
    print(f"\n   per turn: synchronous {per_turn.synchronous}  "
          f"deferred {per_turn.deferred}  total {per_turn.total}")
    print(f"   blocking share: {per_turn.blocking_share:.0%}")


if __name__ == "__main__":
    main()
