"""Count what can be scored before scoring anything."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.fixtures import load_gold

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

coverage = _solution.coverage
seams = _solution.seams
stages = _solution.stages


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.seams()


def test_seven_of_nine_seams_are_checkable() -> None:
    found = seams()
    assert coverage(found) == (7, 9)


def test_twenty_three_of_twenty_five_assertions() -> None:
    """Counting seams instead hides that one gap is the compliance one."""
    found = seams()
    assert sum(s.items for s in found) == 25
    assert sum(s.items for s in found if s.checkable) == 23


def test_the_uncheckable_two(  ) -> None:
    uncheckable = {s.name for s in seams() if not s.checkable}
    assert uncheckable == {"deletion_request", "persona"}


def test_must_also_remove_is_five_english_sentences() -> None:
    clauses = load_gold()["deletion_request"]["must_also_remove"]
    assert len(clauses) == 5
    assert all(isinstance(c, str) and " " in c for c in clauses)


def test_the_item_counts_match_gold() -> None:
    gold = load_gold()
    by_name = {s.name: s.items for s in seams()}
    for key in ("entities", "supersessions", "relative_time", "pii",
                "procedures", "shared_memory"):
        assert by_name[key] == len(gold[key]), key


def test_seven_stages_between_the_turn_and_the_answer() -> None:
    assert len(stages()) == 7
    assert stages()[0] == "extract"
    assert stages()[-1] == "assemble"


def test_supersessions_are_checkable_because_they_are_dated(  ) -> None:
    """A moving ground truth needs a date, not a value."""
    for entry in load_gold()["supersessions"]:
        stated = entry.get("original") or entry.get("addition")
        assert "session" in stated


def test_the_exam_is_one_assertion_of_twenty_five() -> None:
    final = next(s for s in seams() if s.name == "final_question")
    assert final.items == 1
    assert final.checkable
