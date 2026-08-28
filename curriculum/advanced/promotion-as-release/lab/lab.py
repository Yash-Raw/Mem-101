"""Lab: stage a consolidation, measure it, and be able to undo it.

    uv run python curriculum/advanced/promotion-as-release/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from memlab.types import Memory


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
    raise NotImplementedError("implement stage")


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
    raise NotImplementedError("implement preview")


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
    raise NotImplementedError("implement rollback")


NOW = datetime(2026, 8, 27, tzinfo=UTC)


def _fingerprint(memories):
    return sorted(
        (m.id, m.invalid_at, m.superseded_by, m.valid_to, m.tier.value)
        for m in memories
    )


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.eval.exam import exam_from_context
    from memlab.pipeline import at
    from memlab.sleep.reflect import reflect
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    pipeline = at("A2")
    store = JsonlStore("/tmp/memlab-release.jsonl")
    store.clear()
    ingest(store, scope, pipeline)

    def lowest_passing(memories):
        for budget in range(40, 90):
            if exam_from_context(
                memories, scope, k=5, pipeline=pipeline, budget=budget
            ).is_correct:
                return budget
        return None

    baseline = _fingerprint(store.all())
    staged = stage(store.all(), lambda ms: reflect(ms, scope), NOW)
    print(f"staged: {staged.label}   adds {len(staged.added)}   "
          f"retires {len(staged.retired)}   base {len(staged.base_ids)}")

    verdict = evaluate(
        store.all(),
        preview(store.all(), staged, NOW, pipeline.decay),
        lowest_passing,
    )
    print(f"verdict: before {verdict.before}   after {verdict.after}   "
          f"delta {verdict.delta:+d}   better={verdict.better}")
    print(f"store untouched by staging: {len(store.all())} memories\n")

    print("   the step that was missing:\n")
    for label, finalize in (("preview without the finalize step", None),
                            ("preview with it", pipeline.decay)):
        result = lowest_passing(preview(store.all(), staged, NOW, finalize))
        print(f"   {label:38}{result if result else 'never passes':>14}")

    promote(store, staged, NOW, pipeline.decay)
    print(f"   {'what promote actually wrote':38}{lowest_passing(store.all()):>14}")

    rollback(store, staged)
    print(f"\n   rolled back                           "
          f"{lowest_passing(store.all()):>14}")
    print(f"   store identical: {_fingerprint(store.all()) == baseline}")

    moved = stage(store.all(), lambda ms: reflect(ms, scope), NOW)
    store.replace(store.all()[:-1])
    try:
        promote(store, moved, NOW, pipeline.decay)
    except ValueError as exc:
        print(f"\n   promoting against a moved base: {exc}")


if __name__ == "__main__":
    main()
