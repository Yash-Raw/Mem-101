"""Lab: count what stands between a change and an undetected regression.

    uv run python curriculum/advanced/regression-testing-state/lab/lab.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_TEST = re.compile(r"^def test_", re.MULTILINE)
_PINNED = re.compile(r"assert[^\n]*==\s*[0-9]")


@dataclass(frozen=True)
class Inventory:
    """What stands between a change and an undetected regression."""

    lab_files: int
    capstone_files: int
    tests: int
    pinned: int
    snapshots: int

    @property
    def pinned_share(self) -> float:
        return round(self.pinned / self.tests, 3) if self.tests else 0.0


def inventory(root: Path, snapshots: int) -> Inventory:
    """Count the guards. Reading the tests, not running them."""
    raise NotImplementedError("implement inventory")


def golden_conversation_required(pinned: int) -> str:
    """Why a fixed corpus is not optional once numbers are pinned.

    With a deterministic corpus a pinned literal is a claim about the system.
    Without one it is a claim about the corpus *and* the system, and it fails
    on every ingest for reasons nobody can attribute.
    """
    raise NotImplementedError("implement golden_conversation_required")


def main() -> None:
    from memlab.pipeline import ADVANCED_MODULES, MODULES

    root = Path(__file__).resolve().parents[4]
    counts = inventory(root, len(MODULES) + len(ADVANCED_MODULES))

    print(f"   lab test files      {counts.lab_files}")
    print(f"   capstone test files {counts.capstone_files}")
    print(f"   test functions      {counts.tests}")
    print(f"   pinned literals     {counts.pinned}   "
          f"({counts.pinned_share:.0%} of tests)")
    print(f"   module snapshots    {counts.snapshots}")
    print(f"\n   {golden_conversation_required(counts.pinned)}")


if __name__ == "__main__":
    main()
