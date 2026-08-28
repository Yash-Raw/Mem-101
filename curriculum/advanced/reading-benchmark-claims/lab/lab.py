"""Lab: read a benchmark claim, starting with your own.

    uv run python curriculum/advanced/reading-benchmark-claims/lab/lab.py
"""

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
    raise NotImplementedError("implement about")


def questions() -> tuple[str, ...]:
    """What to ask of any benchmark number, including your own."""
    raise NotImplementedError("implement questions")


STAGES = ("extract", "resolve", "arbitrate", "anchor")
ABSENT = ("dedupe", "decay", "rank")
CORPUS = "one corpus, one persona, 24 turns"
PROFILES = ("I4", "I6", "I8", "A1", "A2", "A3")


def main() -> None:
    import pathlib
    import tempfile

    from memlab.eval.suite import run
    from memlab.types import Scope

    rows = run(PROFILES, Scope(user="priya"), pathlib.Path(tempfile.mkdtemp()))
    claim = about(rows, STAGES, ABSENT, CORPUS)

    print(f"   headline : memlab v0.3 {claim.headline}")
    print(f"   moved    : {list(claim.moved)}   "
          f"({claim.informative} of {len(STAGES)} informative)")
    print(f"   flat     : {list(claim.flat)}")
    print(f"   absent   : {list(claim.absent)}")
    print(f"   corpus   : {claim.corpus}")
    print(f"   honest   : {claim.honest}")

    print()
    for question in questions():
        print(f"   - {question}")


if __name__ == "__main__":
    main()
