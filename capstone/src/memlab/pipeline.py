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
DecayFn = Callable[[list[Memory]], list[Memory]]
RankFn = Callable[[str, list[Memory], Scope], list]

AssembleFn = Callable[..., str]
AnchorFn = Callable[[list[Memory], dict], list[Memory]]


@dataclass(frozen=True)
class Pipeline:
    """What runs, and what does not, at this level."""

    name: str
    extract: ExtractFn
    resolve: ResolveFn | None = None          # I2/I4: entity + conflict resolution
    consolidate: ConsolidateFn | None = None  # I3: dedupe, summarise, promote
    live_only: bool = False                   # I4: filter retired memories on read
    ingest_agent_writes: bool = False         # I1: admit shared-scope hearsay
    decay: DecayFn | None = None              # I5: score salience, move tiers
    rank: RankFn | None = None                # I6: hybrid scoring; None = plain cosine
    vectors: object | None = None             # I7: a VectorIndex; None = recompute
    assemble: AssembleFn | None = None        # I8: budgeted packing; None = assemble.simple
    anchor: AnchorFn | None = None            # A1: resolve relative time against the turn clock
    bitemporal: bool = False                  # A1: split valid_to from invalid_at
    sleep: object | None = None               # A2: a Schedule; None = consolidate inline
    admit: object | None = None               # A3: a WritePolicy; None = accept any write

    def with_stage(self, **changes) -> Pipeline:
        """Turn a stage on. Lessons use this rather than editing the factories."""
        return replace(self, **changes)


def beginner() -> Pipeline:
    """Level 1 as shipped: extract, store, retrieve, assemble. Nothing else.

    This configuration is load-bearing. A dozen exact figures are quoted in the
    Beginner lessons and pinned by capstone/tests/test_v1_failures.py -- rank 1
    vs rank 18, 36 memories from 24 turns, the k-sweep table. If a change here
    moves one of them, that is a build break, not a number to update.
    """
    return Pipeline(name="beginner", extract=naive_extract)


# Each module switches on exactly one capability, so the improvement it claims
# is attributable to it alone -- and so a lesson's measured numbers stay true
# after later modules land. `at("I1")` is the system as I1 left it, forever.
MODULES = ("I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8")

# Level 3 layers on top of Level 2 rather than replacing it: `advanced("A1")`
# is `intermediate("latest")` plus A1's one capability. The same rule holds --
# one module, one switch, so a claimed improvement is attributable to it alone.
ADVANCED_MODULES = ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9")


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
    if "I4" in reached:
        p = replace(
            p,
            consolidate=_resolve_dedupe_reconcile,  # + retire superseded beliefs
            live_only=True,                         # and stop retrieving them
        )
    if "I5" in reached:
        p = replace(p, decay=_score_and_decay)      # salience, ageing, tiering
    if "I6" in reached:
        p = replace(p, rank=_hybrid_search)         # filter, formulate, rank, merge
    if "I7" in reached:
        from .store.vector import VectorIndex

        p = replace(p, vectors=VectorIndex())       # embed once per memory, not per query
    if "I8" in reached:
        p = replace(p, assemble=_budgeted_assemble)  # priced elements, pinned coverage
    return p


def _budgeted_assemble(hits, budget_tokens: int = 400) -> str:
    """Compact framing, year-precision dates, slot coverage pinned."""
    from .assemble.budget import pack
    from .assemble.value import COMPACT_HEADER

    return pack(
        hits, budget_tokens=budget_tokens, header=COMPACT_HEADER, pin=True,
        precision="year",
    ).text


def _hybrid_search(query, memories, scope, k=5, index=None):
    """The composed read path: scope -> formulate -> slot+similarity -> merge."""
    from .retrieve.scoped import search

    return search(query, memories, scope, k=k, index=index)


def _score_and_decay(memories):
    """Importance, then ageing, then the tier cap. Nothing is removed."""
    from .fixtures import load_turns
    from .forget import budget, decay, salience

    turns = {f"s{t['session']}:{t['ts']}": t["text"] for t in load_turns(user_only=True)}
    aged = decay.apply(salience.apply(memories, turns))
    capped, _evictions = budget.enforce(aged)
    return capped


def _resolve_then_dedupe(memories):
    """Order matters: dedupe compares entities, so resolution runs first."""
    from .evolve.dedupe import dedupe

    return dedupe(resolve_all(memories))


def _resolve_dedupe_reconcile(memories):
    """The full write path. Resolve identities, collapse restatements, then
    reconcile what genuinely disagrees."""
    return _reconcile(memories, bitemporal=False)


def _reconcile(memories, bitemporal: bool):
    from .types import Scope

    consolidated = _resolve_then_dedupe(memories)
    scope = Scope(user=consolidated[0].scope.user) if consolidated else None
    if scope is None:
        return consolidated
    from .evolve.supersede import reconcile

    return reconcile(consolidated, scope, bitemporal=bitemporal).memories


def advanced(through: str = "latest") -> Pipeline:
    """Level 3, optionally as it stood at the end of a given module.

    Starts from Level 2 complete. Every `@I*` snapshot must stay byte-identical
    after this function grows -- an Advanced capability that moves an
    Intermediate figure is a build break, not a number to re-quote.
    """
    if through != "latest" and through not in ADVANCED_MODULES:
        raise ValueError(
            f"unknown module {through!r} (known: {', '.join(ADVANCED_MODULES)})"
        )
    reached = (
        ADVANCED_MODULES
        if through == "latest"
        else ADVANCED_MODULES[: ADVANCED_MODULES.index(through) + 1]
    )
    p = replace(intermediate(), name=f"advanced@{through}")
    if "A1" in reached:
        from .temporal.anchor import anchor_all

        p = replace(
            p,
            consolidate=_anchor_then_reconcile,
            bitemporal=True,     # valid_to and invalid_at are different instants
            anchor=anchor_all,   # and valid_from is read off the sentence
        )
    if "A2" in reached:
        from .sleep.schedule import Schedule

        # Consolidate on the turns that contest a slot, and defer the rest.
        # `None` keeps the batch behaviour every earlier snapshot was
        # measured against -- `ingest()` consolidates once regardless.
        p = replace(p, sleep=Schedule.default())
    if "A3" in reached:
        from .agents.authorise import WritePolicy

        # Who may write what, where. `None` accepts anything, which is what
        # every earlier snapshot was measured against.
        p = replace(p, admit=WritePolicy.default())
    return p


def _resolve_dedupe_reconcile_bitemporal(memories):
    """The Level 2 write path, with the two retirement clocks kept apart.

    A1 as `validity-intervals` left it: the axes separated, and nothing yet
    reading an event date off the language. Lessons pin this explicitly with
    `at("A1").with_stage(anchor=None, consolidate=...)` when they need to
    measure the model before the parser closed the gap.
    """
    return _reconcile(memories, bitemporal=True)


def _anchor_then_reconcile(memories):
    """Anchor relative references first -- reconciliation compares event times.

    Order matters and it is not obvious. Arbitration is recency-wins on the
    event clock, so resolving "last month" after the fact has already lost is
    resolving it too late.
    """
    from .temporal.anchor import anchor_all

    return _reconcile(anchor_all(memories), bitemporal=True)


def at(module: str) -> Pipeline:
    """The pipeline as it stood at the end of `module` -- `I*` or `A*`."""
    if module.startswith("A"):
        return advanced(through=module)
    return intermediate(through=module)


PROFILES: dict[str, Callable[[], Pipeline]] = {
    "beginner": beginner,
    "intermediate": intermediate,
    "advanced": advanced,
}


def get(name: str) -> Pipeline:
    if name not in PROFILES:
        known = ", ".join(sorted(PROFILES))
        raise ValueError(f"unknown profile {name!r} (known: {known})")
    return PROFILES[name]()
