"""Lab: count what can be scored before scoring anything.

    uv run python curriculum/advanced/why-memory-eval-is-hard/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Seam:
    """One thing `gold.yml` asserts, and whether it is machine-checkable."""

    name: str
    items: int
    checkable: bool
    why: str


def seams() -> list[Seam]:
    """What the answer key covers, and what a harness can actually score.

    `checkable` is the load-bearing column. A seam is checkable when its gold
    entry states a value a program can compare against the store. The rest are
    real and are prose -- a note explaining what to look for, which is a
    reviewer's instruction, not a test.
    """
    raise NotImplementedError("implement seams")


def coverage(seams_: list[Seam]) -> tuple[int, int]:
    """(checkable seams, total seams)."""
    raise NotImplementedError("implement coverage")


def stages() -> tuple[str, ...]:
    """The write and read stages a wrong answer implicates, in order.

    Seven. The exam is a single boolean over all of them, which is why this
    course reached for module snapshots -- attributing a regression by
    bisecting the pipeline rather than by measuring any stage directly.
    """
    raise NotImplementedError("implement stages")


def main() -> None:
    found = seams()
    print(f"   {'seam':18}{'items':>6}{'checkable':>11}  why")
    for seam in found:
        print(f"   {seam.name:18}{seam.items:>6}{seam.checkable!s:>11}  "
              f"{seam.why[:52]}")

    checkable, total = coverage(found)
    assertions = sum(s.items for s in found)
    scored = sum(s.items for s in found if s.checkable)
    print(f"\n   checkable: {checkable} of {total} seams, "
          f"{scored} of {assertions} assertions")
    print(f"   stages a wrong answer implicates: {len(stages())}")
    print(f"   {list(stages())}")


if __name__ == "__main__":
    main()
