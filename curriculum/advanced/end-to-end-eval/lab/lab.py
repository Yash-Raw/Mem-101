"""Lab: one battery over every profile, and what it cannot see.

    uv run python curriculum/advanced/end-to-end-eval/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.eval.exam import exam_from_context
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
    raise NotImplementedError("implement run")


def flat(rows: list[Row], stage: str) -> bool:
    """Did this metric report the same value for every profile?

    A flat column is not a passing grade. It means the battery cannot see
    the difference between the profiles, which is worth knowing before
    anyone cites it as evidence that a module worked.
    """
    raise NotImplementedError("implement flat")


def regressions(rows: list[Row]) -> list[tuple[str, str]]:
    """(profile, metric) pairs where a later profile scored worse."""
    raise NotImplementedError("implement regressions")


PROFILES = ("I4", "I6", "I8", "A1", "A2", "A3")
STAGES = ("extract", "resolve", "arbitrate", "anchor")


def main() -> None:
    import pathlib
    import tempfile

    scope = Scope(user="priya")
    root = pathlib.Path(tempfile.mkdtemp())
    rows = run(PROFILES, scope, root)

    header = f"   {'profile':9}{'mem':>5}{'live':>6}{'belief':>8}{'budget':>8}"
    print(header + "".join(f"{s:>11}" for s in STAGES))
    for row in rows:
        cells = "".join(
            f"{(f'{row.get(s):.3f}' if row.get(s) is not None else '--'):>11}"
            for s in STAGES
        )
        print(f"   {row.profile:9}{row.memories:>5}{row.live:>6}"
              f"{row.belief_exam!s:>8}{row.lowest_budget!s:>8}" + cells)

    print(f"\n   flat across every profile: {[s for s in STAGES if flat(rows, s)]}")
    print(f"   regressions: {regressions(rows)}")


if __name__ == "__main__":
    main()
