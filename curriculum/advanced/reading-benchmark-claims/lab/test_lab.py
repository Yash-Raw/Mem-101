"""Apply the reading to your own claim first."""
from __future__ import annotations

import pathlib

import pytest
from memlab import labkit
from memlab.eval.suite import run
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

about = _solution.about
questions = _solution.questions

PRIYA = Scope(user="priya")
STAGES = ("extract", "resolve", "arbitrate", "anchor")
ABSENT = ("dedupe", "decay", "rank")
CORPUS = "one corpus, one persona, 24 turns"
PROFILES = ("I4", "I6", "I8", "A1", "A2", "A3")


@pytest.fixture(scope="module")
def claim(tmp_path_factory):
    rows = run(PROFILES, PRIYA, tmp_path_factory.mktemp("rb"))
    return about(rows, STAGES, ABSENT, CORPUS)


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.questions()


def test_one_of_four_metrics_is_informative(claim) -> None:
    assert claim.moved == ("anchor",)
    assert claim.informative == 1
    assert len(STAGES) == 4


def test_three_metrics_were_already_saturated(claim) -> None:
    """Correct, and empty as evidence for anything in Level 3."""
    assert set(claim.flat) == {"extract", "resolve", "arbitrate"}


def test_moved_and_flat_partition_the_metrics(claim) -> None:
    assert set(claim.moved) | set(claim.flat) == set(STAGES)
    assert not set(claim.moved) & set(claim.flat)


def test_the_claim_carries_all_four_qualifiers(claim) -> None:
    assert claim.honest
    assert claim.absent == ABSENT
    assert "24 turns" in claim.corpus


def test_a_claim_missing_a_qualifier_is_not_honest(claim) -> None:
    stripped = claim.__class__(
        headline=claim.headline, moved=claim.moved, flat=claim.flat,
        absent=(), corpus=claim.corpus,
    )
    assert not stripped.honest
    no_corpus = claim.__class__(
        headline=claim.headline, moved=claim.moved, flat=claim.flat,
        absent=claim.absent, corpus="",
    )
    assert not no_corpus.honest


def test_moved_is_computed_not_asserted(tmp_path_factory) -> None:
    """Two profiles that agree on everything yield no informative metric."""
    rows = run(("A2", "A3"), PRIYA, tmp_path_factory.mktemp("rb2"))
    identical = about(rows, STAGES, ABSENT, CORPUS)
    assert identical.moved == ()
    assert identical.informative == 0


def test_four_questions(  ) -> None:
    asked = questions()
    assert len(asked) == 4
    assert all(q.endswith("?") for q in asked)


def test_the_lesson_keeps_product_names_in_a_landscape_block() -> None:
    """C-rule: no vendor or benchmark name outside a marked block."""
    text = (
        pathlib.Path(__file__).resolve().parents[1] / "index.md"
    ).read_text()
    inside = text.split("<!-- landscape:begin -->")[1].split(
        "<!-- landscape:end -->"
    )[0]
    for name in ("LoCoMo", "LongMemEval", "BEAM"):
        assert text.count(name) == inside.count(name), name
