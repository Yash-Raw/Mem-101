"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass

from memlab.app.chat import ingest
from memlab.eval.components import report
from memlab.eval.exam import exam_answer, exam_from_context
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope


@dataclass(frozen=True)
class Row:
    """One profile's results across the whole battery."""

    profile: str
    memories: int
    live: int
    belief_exam: bool
    lowest_budget: int | None
    components: dict[str, float | None]

    def get(self, stage: str) -> float | None:
        return self.components.get(stage)


def _lowest_passing(memories, scope, pipeline, lo: int = 30, hi: int = 90) -> int | None:
    for budget in range(lo, hi):
        if exam_from_context(
            memories, scope, k=5, pipeline=pipeline, budget=budget
        ).is_correct:
            return budget
    return None


def run(profiles: tuple[str, ...], scope: Scope, root) -> list[Row]:
    """Build each profile from scratch and score it identically.

    From scratch, every time. Sharing a store between profiles is how a
    later profile inherits an earlier one's consolidation and reports an
    improvement it did not make.
    """
    rows = []
    for name in profiles:
        pipeline = at(name)
        store = JsonlStore(root / f"{name}.jsonl")
        store.clear()
        ingest(store, scope, pipeline)
        if pipeline.vectors is not None:
            pipeline.vectors.index(store.all())
        memories = store.all()
        rows.append(
            Row(
                profile=name,
                memories=len(memories),
                live=sum(m.is_live for m in memories),
                belief_exam=exam_answer(memories, scope).is_correct,
                lowest_budget=_lowest_passing(memories, scope, pipeline),
                components={
                    m.stage: m.rate for m in report(memories, scope) if m.scorable
                },
            )
        )
    return rows


def flat(rows: list[Row], stage: str) -> bool:
    """Did this metric report the same value for every profile?

    A flat column is not a passing grade. It means the battery cannot see
    the difference between the profiles, which is worth knowing before
    anyone cites it as evidence that a module worked.
    """
    values = [r.get(stage) for r in rows]
    return len(set(values)) == 1


def regressions(rows: list[Row]) -> list[tuple[str, str]]:
    """(profile, metric) pairs where a later profile scored worse."""
    out = []
    for earlier, later in zip(rows, rows[1:], strict=False):
        for stage, value in later.components.items():
            was = earlier.get(stage)
            if was is not None and value is not None and value < was:
                out.append((later.profile, stage))
        if earlier.lowest_budget and later.lowest_budget:
            if later.lowest_budget > earlier.lowest_budget:
                out.append((later.profile, "lowest_budget"))
    return out
