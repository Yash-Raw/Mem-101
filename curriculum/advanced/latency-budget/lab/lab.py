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


def budget(extract_calls: int, consolidations: int, turns: int) -> Budget:
    """Per-turn split, from counts the earlier modules already measured.

    `consolidations` is the A2 gate's figure -- the turns on which
    arbitration could not wait. Everything else in the write path is
    deferred, so the blocking cost is extraction plus that fraction.
    """
    raise NotImplementedError("implement budget")


EXTRACT_CALLS = 48   # cost-model, full ingest
CONSOLIDATIONS = 11  # sleep-time-compute, the contested-slot gate
TURNS = 24


def main() -> None:
    stages = split()
    for stage in stages:
        print(f"   {stage.name:11}{stage.when.value:14}{stage.why[:58]}")

    synchronous = sum(1 for s in stages if s.when is When.SYNCHRONOUS)
    print(f"\n   synchronous stages: {synchronous} of {len(stages)}")

    per_turn = budget(EXTRACT_CALLS, CONSOLIDATIONS, TURNS)
    print(f"   per turn: synchronous {per_turn.synchronous}  "
          f"deferred {per_turn.deferred}  total {per_turn.total}")
    print(f"   blocking share: {per_turn.blocking_share:.0%}")


if __name__ == "__main__":
    main()
