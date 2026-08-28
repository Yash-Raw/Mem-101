"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Claim:
    """A score, and the four things it does not say."""

    headline: str
    moved: tuple[str, ...]
    flat: tuple[str, ...]
    absent: tuple[str, ...]
    corpus: str

    @property
    def informative(self) -> int:
        """Metrics that actually distinguish the systems being compared."""
        return len(self.moved)

    @property
    def honest(self) -> bool:
        """Does the claim carry all four qualifiers?"""
        return bool(self.moved or self.flat) and bool(self.absent) and bool(self.corpus)


def about(rows, stages: tuple[str, ...], absent: tuple[str, ...], corpus: str) -> Claim:
    """Build the claim this suite can actually support.

    `moved` is computed, not asserted: a metric qualifies only if two of the
    compared profiles disagree on it. That is the line between a result and
    a number.
    """
    moved, flat = [], []
    for stage in stages:
        values = {r.get(stage) for r in rows}
        (moved if len(values) > 1 else flat).append(stage)
    return Claim(
        headline=(
            f"scores {max((r.get(s) or 0) for r in rows for s in stages):.3f} "
            f"on {len(stages)} metrics across {len(rows)} profiles"
        ),
        moved=tuple(moved),
        flat=tuple(flat),
        absent=absent,
        corpus=corpus,
    )


def questions() -> tuple[str, ...]:
    """What to ask of any benchmark number, including your own."""
    return (
        "which metrics differ between the systems compared?",
        "which were already saturated before the change?",
        "which stages have no metric at all?",
        "on what corpus, and how much of it?",
    )
