"""Reference solution."""

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
    return [
        Stage("extract", When.SYNCHRONOUS,
              "a memory not extracted cannot be retrieved on the next turn"),
        Stage("resolve", When.SYNCHRONOUS,
              "entity links are needed to file the memory correctly"),
        Stage("dedupe", When.DEFERRED,
              "a duplicate is retrievable; it is just wasteful"),
        Stage("arbitrate", When.SYNCHRONOUS,
              "only on a contested slot -- the A2 gate; otherwise deferred"),
        Stage("decay", When.DEFERRED,
              "salience drifts slowly; a turn's delay is invisible"),
        Stage("summarise", When.DEFERRED,
              "nothing reads a summary that does not exist yet"),
        Stage("reflect", When.DEFERRED,
              "and unwired anyway -- A2.3 measured it as a regression"),
    ]


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
    return Budget(
        synchronous=round(extract_calls / turns, 2),
        deferred=round(consolidations / turns, 2),
    )
