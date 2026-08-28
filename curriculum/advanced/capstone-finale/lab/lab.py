"""Lab: ship it, and write down what is still wrong.

    uv run python curriculum/advanced/capstone-finale/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Release:
    version: str
    lessons: int
    tests: int
    exams: dict[str, str]
    cost: dict[str, str]
    open_items: tuple[tuple[str, str], ...]

    @property
    def complete(self) -> bool:
        """A release is not "done"; it is shipped with its gaps written down."""
        return bool(self.open_items)


def report(lessons: int, tests: int) -> Release:
    raise NotImplementedError("implement report")


def unfinished(release: Release) -> int:
    raise NotImplementedError("implement unfinished")


def lines(release: Release) -> list[str]:
    raise NotImplementedError("implement lines")


def main() -> None:
    import pathlib
    import re

    # Counted from source rather than by running pytest: this lab is itself
    # run by the test suite, and shelling out to pytest from inside it would
    # recurse.
    root = pathlib.Path(__file__).resolve().parents[4]
    lessons = len(list((root / "curriculum").glob("*/*/index.md")))
    tests = sum(
        len(re.findall(r"^def test_", path.read_text(), re.MULTILINE))
        for path in [
            *(root / "curriculum").rglob("lab/test_lab.py"),
            *(root / "capstone" / "tests").glob("test_*.py"),
        ]
    )

    for line in lines(report(lessons, tests)):
        print("  " + line)


if __name__ == "__main__":
    main()
