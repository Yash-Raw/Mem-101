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

from .entity.resolve import resolve_all
from .extract.naive import extract as naive_extract
from .extract.pipeline import extract as staged_extract
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


# Each module switches on exactly one capability, so the improvement it claims
# is attributable to it alone -- and so a lesson's measured numbers stay true
# after later modules land. `at("I1")` is the system as I1 left it, forever.
MODULES = ("I1", "I2", "I3", "I4")


def intermediate(through: str = "latest") -> Pipeline:
    """Level 2, optionally as it stood at the end of a given module.

    Lesson tests pin numbers measured against their own module's snapshot.
    Without that, I3's deduplication silently invalidates every count I1
    quoted, and the only remedies are re-quoting prose on every commit or
    letting the numbers rot. Both are worse than a checkpoint.
    """
    if through != "latest" and through not in MODULES:
        raise ValueError(f"unknown module {through!r} (known: {', '.join(MODULES)})")
    reached = MODULES if through == "latest" else MODULES[: MODULES.index(through) + 1]

    p = replace(beginner(), name=f"intermediate@{through}")

    if "I1" in reached:
        p = replace(
            p,
            extract=staged_extract,        # staged, with event -> state
            ingest_agent_writes=True,      # shared-scope writes carry authority
        )
    if "I2" in reached:
        p = replace(p, consolidate=resolve_all)          # resolution needs the whole store
    if "I3" in reached:
        p = replace(p, consolidate=_resolve_then_dedupe)  # + collapse restatements
    return p


def _resolve_then_dedupe(memories):
    """Order matters: dedupe compares entities, so resolution runs first."""
    from .evolve.dedupe import dedupe

    return dedupe(resolve_all(memories))


def at(module: str) -> Pipeline:
    """The intermediate pipeline as it stood at the end of `module`."""
    return intermediate(through=module)


PROFILES: dict[str, Callable[[], Pipeline]] = {
    "beginner": beginner,
    "intermediate": intermediate,
}


def get(name: str) -> Pipeline:
    if name not in PROFILES:
        known = ", ".join(sorted(PROFILES))
        raise ValueError(f"unknown profile {name!r} (known: {known})")
    return PROFILES[name]()
