"""The regression discipline this course already runs, made countable.

`end-to-end-eval` compares profiles at one moment. The harder problem is
comparing the *same* profile across time -- the change you are about to make
against the system as it stands -- and this repository has been doing that
since I3 without calling it evaluation.

Three mechanisms, all already here:

    pinned assertions   331 assertions comparing against a literal number
    module snapshots    17 checkpoints; `at("I3")` is the system I3 left
    a golden corpus     one conversation, every lab, every level

The pinned numbers are the interesting one. A memory system's outputs are
counts, ranks and scores rather than pass/fail, so a test asserting `== 37`
is a *snapshot of behaviour* -- and 331 of them is a regression suite nobody
designed, assembled one lesson at a time by writing down what was measured.

What makes them tolerable is the third mechanism. A golden conversation means
the numbers are reproducible; without it, 331 literals would be 331 things to
update on every run.
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
    labs = sorted((root / "curriculum").rglob("lab/test_lab.py"))
    capstone = sorted((root / "capstone" / "tests").glob("test_*.py"))
    tests = pinned = 0
    for path in [*labs, *capstone]:
        text = path.read_text()
        tests += len(_TEST.findall(text))
        pinned += len(_PINNED.findall(text))
    return Inventory(
        lab_files=len(labs),
        capstone_files=len(capstone),
        tests=tests,
        pinned=pinned,
        snapshots=snapshots,
    )


def golden_conversation_required(pinned: int) -> str:
    """Why a fixed corpus is not optional once numbers are pinned.

    With a deterministic corpus a pinned literal is a claim about the system.
    Without one it is a claim about the corpus *and* the system, and it fails
    on every ingest for reasons nobody can attribute.
    """
    return (
        f"{pinned} pinned literals are only maintainable against a fixed "
        f"corpus; with a changing one, each is two claims at once"
    )
