"""A regression suite nobody designed, counted.

These counts grow with every lesson added, so the assertions are floors and
relationships rather than equalities -- except `snapshots`, which is a fixed
property of the pipeline. The lesson quotes the values at the time it was
written and the lab prints the live ones; if they have drifted, the course
has grown, which is the only thing that should move them.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from memlab import labkit
from memlab.pipeline import ADVANCED_MODULES, MODULES

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

golden_conversation_required = _solution.golden_conversation_required
inventory = _solution.inventory

ROOT = Path(__file__).resolve().parents[4]
SNAPSHOTS = len(MODULES) + len(ADVANCED_MODULES)


@pytest.fixture(scope="module")
def counts():
    return inventory(ROOT, SNAPSHOTS)


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.inventory(ROOT, SNAPSHOTS)


def test_the_counts_only_grow(counts) -> None:
    """Floors, taken when this lesson was written."""
    assert counts.lab_files >= 72
    assert counts.capstone_files >= 3
    assert counts.tests >= 646
    assert counts.pinned >= 331


def test_about_half_the_tests_pin_a_literal(counts) -> None:
    """The shape the problem forces: outputs are counts, not pass/fail."""
    assert 0.4 <= counts.pinned_share <= 0.6


def test_seventeen_module_snapshots(counts) -> None:
    """Fixed by the pipeline, not by how many lessons exist."""
    assert counts.snapshots == 17
    assert MODULES[0] == "I1"
    assert ADVANCED_MODULES[-1] == "A9"


def test_every_lab_has_a_test_file(counts) -> None:
    labs = sorted((ROOT / "curriculum").rglob("lab/lab.py"))
    assert counts.lab_files == len(labs), "a lab with no test pins nothing"


def test_the_reason_a_frozen_corpus_is_required(counts) -> None:
    text = golden_conversation_required(counts.pinned)
    assert str(counts.pinned) in text
    assert "two claims" in text


def test_inventory_runs_nothing(counts) -> None:
    """Answerable before a change, not after the suite has passed."""
    assert counts.tests > 0
    assert isinstance(counts.pinned_share, float)
