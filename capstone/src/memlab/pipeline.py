"""Level profiles: which stages of the memory lifecycle are switched on.

The course builds one system across three levels, and every lesson needs the
naive version to stay executable -- a claim like "supersession fixes staleness"
is only meaningful against a baseline you can still run. So `memlab` is not
three codebases. It is one, with the stages a level has not reached yet turned
off.

    memlab.app.chat --profile beginner       # the system as Level 1 leaves it
    memlab.app.chat --profile intermediate   # with Level 2's machinery on

Adding a stage means filling in a field here, in the lesson that teaches it.
Nothing else moves.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from .extract.naive import extract as naive_extract
from .types import Memory, Scope

ExtractFn = Callable[[dict, Scope], list[Memory]]
ResolveFn = Callable[[list[Memory], list[Memory]], list[Memory]]
ConsolidateFn = Callable[[list[Memory]], list[Memory]]


@dataclass(frozen=True)
class Pipeline:
    """What runs, and what does not, at this level."""

    name: str
    extract: ExtractFn
    resolve: ResolveFn | None = None          # I2/I4: entity + conflict resolution
    consolidate: ConsolidateFn | None = None  # I3: dedupe, summarise, promote
    live_only: bool = False                   # I4: filter retired memories on read
    ingest_agent_writes: bool = False         # I4: admit shared-scope hearsay

    def with_stage(self, **changes) -> Pipeline:
        """Turn a stage on. Lessons use this rather than editing the factories."""
        return replace(self, **changes)


def beginner() -> Pipeline:
    """Level 1 as shipped: extract, store, retrieve, assemble. Nothing else.

    This configuration is load-bearing. A dozen exact figures are quoted in the
    Beginner lessons and pinned by capstone/tests/test_v1_failures.py -- rank 1
    vs rank 18, 36 memories from 25 turns, the k-sweep table. If a change here
    moves one of them, that is a build break, not a number to update.
    """
    return Pipeline(name="beginner", extract=naive_extract)


def intermediate() -> Pipeline:
    """Level 2. Identical to beginner until the lessons that fill it in.

    Each of I1-I4 switches on exactly one stage, so the improvement it claims is
    attributable to it alone.
    """
    return replace(beginner(), name="intermediate")


PROFILES: dict[str, Callable[[], Pipeline]] = {
    "beginner": beginner,
    "intermediate": intermediate,
}


def get(name: str) -> Pipeline:
    if name not in PROFILES:
        known = ", ".join(sorted(PROFILES))
        raise ValueError(f"unknown profile {name!r} (known: {known})")
    return PROFILES[name]()
