"""The release report, and why its last section is the load-bearing one."""
from __future__ import annotations

import pathlib
import re

import pytest
from memlab import labkit

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

lines = _solution.lines
report = _solution.report
unfinished = _solution.unfinished

ROOT = pathlib.Path(__file__).resolve().parents[4]


@pytest.fixture(scope="module")
def counts():
    lessons = len(list((ROOT / "curriculum").glob("*/*/index.md")))
    tests = sum(
        len(re.findall(r"^def test_", path.read_text(), re.MULTILINE))
        for path in [
            *(ROOT / "curriculum").rglob("lab/test_lab.py"),
            *(ROOT / "capstone" / "tests").glob("test_*.py"),
        ]
    )
    return lessons, tests


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.report(84, 742)


def test_the_course_is_eighty_four_lessons(counts) -> None:
    lessons, _tests = counts
    assert lessons == 84


def test_six_open_items(counts) -> None:
    release = report(*counts)
    assert unfinished(release) == 6


def test_a_release_is_complete_when_it_has_gaps(counts) -> None:
    """Not a joke: an empty list means nobody looked."""
    release = report(*counts)
    assert release.complete
    empty = release.__class__(
        version=release.version, lessons=release.lessons, tests=release.tests,
        exams=release.exams, cost=release.cost, open_items=(),
    )
    assert not empty.complete


def test_every_open_item_cites_a_lesson(counts) -> None:
    """A gap without a reproduction is a worry."""
    levels = ("beginner", "intermediate", "advanced")
    for _name, detail in report(*counts).open_items:
        lesson = detail.rsplit("— ", 1)[-1].strip()
        assert any(
            (ROOT / "curriculum" / level / lesson / "index.md").exists()
            for level in levels
        ), lesson


def test_every_open_item_carries_a_number(counts) -> None:
    for name, detail in report(*counts).open_items:
        assert re.search(r"\d", detail), name


def test_the_three_exams_are_reported(counts) -> None:
    exams = report(*counts).exams
    assert set(exams) == {"belief", "context (k=5)", "budgeted"}
    assert "51 tokens" in exams["budgeted"]
    assert "43" in exams["budgeted"]


def test_the_cost_lines_match_the_measured_profile(counts) -> None:
    cost = report(*counts).cost
    assert "2.0 model calls" in cost["write path"]
    assert "no model calls" in cost["read path"]
    assert "81%" in cost["blocking"]


def test_two_open_items_are_the_same_stage(counts) -> None:
    """Only a collected list makes that visible."""
    items = report(*counts).open_items
    names = [name for name, _detail in items]
    assert sum(1 for n in names if "extraction" in n) == 2
    text = " ".join(f"{n} {d}" for n, d in items)
    assert "learning-from-outcomes" in text
    assert "memory-attacks" in text


def test_the_report_renders(counts) -> None:
    rendered = lines(report(*counts))
    assert rendered[0].startswith("memlab v0.3")
    assert any(line.strip().startswith("open (6)") for line in rendered)
