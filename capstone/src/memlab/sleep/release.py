"""Consolidation as a controlled deploy: stage, measure, promote or roll back.

`reflection-and-insight` produced three correct, fully traceable beliefs that
made the lowest passing budget worse -- 51 to 55. The problem was not the
beliefs. It was that there was no step between deriving them and having them.

A background job that writes straight into the live store has one outcome and
no way back. Staging separates three questions that were being answered at
once: what would change, is the system better, and can this be undone.

    staged  = stage(store, job)        # computed, not applied
    verdict = evaluate(staged, exam)   # measured against the live store
    promote(store, staged)             # or discard, or roll back later

Rollback is the part that has to be built first, because everything else is
only safe if it exists.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from ..types import Memory


@dataclass(frozen=True)
class Staged:
    """A change computed against a known base, not yet applied."""

    label: str
    base_ids: frozenset[str]
    added: tuple[Memory, ...]
    retired: tuple[str, ...]

    @property
    def size(self) -> int:
        return len(self.added) + len(self.retired)


@dataclass(frozen=True)
class Verdict:
    """What the change did to a measurement, on the same corpus."""

    before: int | None
    after: int | None

    @property
    def better(self) -> bool:
        if self.before is None or self.after is None:
            return self.after is not None
        return self.after < self.before

    @property
    def delta(self) -> int | None:
        if self.before is None or self.after is None:
            return None
        return self.after - self.before


def stage(memories: list[Memory], derive, at: datetime) -> Staged:
    """Compute what a derivation would add and retire, without applying it.

    `derive` returns new memories carrying `derived_from`. Anything named
    there is what the change would subsume -- so the retirement set is read
    off the provenance rather than being specified separately, which is what
    keeps the two from drifting apart.
    """
    added = tuple(derive(memories))
    subsumed = {i for m in added for i in m.derived_from}
    return Staged(
        label=f"derive+{len(added)}",
        base_ids=frozenset(m.id for m in memories),
        added=added,
        retired=tuple(sorted(subsumed)),
    )


def preview(
    memories: list[Memory], staged: Staged, at: datetime, finalize=None
) -> list[Memory]:
    """The store as it *would* be. Nothing is written.

    `finalize` is whatever the pipeline runs after a write -- the decay and
    tiering pass, here. It belongs in the preview because it belongs in the
    application, and the only way to guarantee those agree is for both to
    call this function.

    Leave it out of one and not the other and the release measures a
    different program than it ships: derived beliefs are scored in the
    preview, unscored on disk, and a change that previewed as "five tokens
    worse" arrives as an exam that never passes at any budget.
    """
    retired = set(staged.retired)
    by_source = {i: m.id for m in staged.added for i in m.derived_from}
    out = [
        replace(m, invalid_at=at, valid_to=m.valid_to or at,
                superseded_by=by_source.get(m.id))
        if m.id in retired and m.is_live
        else m
        for m in memories
    ]
    result = [*out, *staged.added]
    return finalize(result) if finalize is not None else result


def evaluate(before: list[Memory], after: list[Memory], measure) -> Verdict:
    """Run the same measurement over both. `measure` returns a number or None.

    The measurement has to be the one that matters, and on this corpus that
    is the lowest passing budget rather than a pass/fail at one budget --
    a change that keeps the exam correct while costing five tokens of
    headroom is a regression that a single-budget check reports as green.
    """
    return Verdict(before=measure(before), after=measure(after))


def promote(store, staged: Staged, at: datetime, finalize=None) -> int:
    """Apply a staged change. Refuses if the base has moved underneath it.

    The base check is `background-job-mechanics`' snapshot rule in its
    strictest form: a release computed against one store must not be applied
    to a different one, because the retirement set was chosen by looking at
    what was live *then*.
    """
    current = store.all()
    if not staged.base_ids <= {m.id for m in current}:
        raise ValueError("base has moved; re-stage against the current store")
    store.replace(preview(current, staged, at, finalize))
    return staged.size


def rollback(store, staged: Staged) -> int:
    """Undo a promoted change: drop what it added, revive what it retired.

    Possible only because supersession never destroyed anything. A store that
    deleted the subsumed memories could not do this at all, which is the
    argument `supersession-not-deletion` made two levels ago, cashed.
    """
    added = {m.id for m in staged.added}
    retired = set(staged.retired)
    out = []
    for memory in store.all():
        if memory.id in added:
            continue
        if memory.id in retired and memory.superseded_by in added:
            memory = replace(memory, invalid_at=None, valid_to=None, superseded_by=None)
        out.append(memory)
    store.replace(out)
    return len(out)
