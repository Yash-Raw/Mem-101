"""Mention detection, and the record that names nobody. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import get
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

audit_mentions = _solution.audit_mentions
descriptors = _solution.descriptors
leading_pronoun = _solution.leading_pronoun
mentions = _solution.mentions
proper_names = _solution.proper_names


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("alias") / "m.jsonl")
    ingest(store, Scope(user="priya"), get("intermediate"))
    return store.all()


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.proper_names("Samira")


def test_proper_names_found() -> None:
    assert proper_names("Samira got a promotion to charge nurse") == ["Samira"]
    assert proper_names("Sammy's commute got worse") == ["Sammy"]


def test_places_are_not_people() -> None:
    """St Aubyn's is a hospital. Found by reading output, not by reasoning."""
    assert proper_names("Priya's partner Sam is a nurse at St. Aubyn's") == ["Sam"]
    assert proper_names("Priya works at Calico Systems") == []
    assert proper_names("Priya moved house") == []


def test_descriptors_denote_a_person_without_naming_one() -> None:
    assert descriptors("My partner Sam is a nurse") == ["my partner"]


def test_only_a_leading_pronoun_counts() -> None:
    assert leading_pronoun("She works nights most of the month") == "she"
    assert leading_pronoun("Priya said she works nights") is None


def test_exactly_one_memory_names_nobody(memories) -> None:
    """The hardest mention in the corpus contains no name at all."""
    orphans = [content for content, _, orphan in audit_mentions(memories) if orphan]
    assert orphans == ["She works nights most of the month"]


def test_dates_and_places_from_agent_writes_are_not_people(memories) -> None:
    """The stop list grew when a new source arrived, not when the code changed."""
    for text in (
        "Priya declined all Friday meetings since March 2026.",
        "Priya has a recurring 1:1 every Tuesday 10:00.",
        "Priya's colleague mentioned she is relocating to Berlin.",
    ):
        assert proper_names(text) == [], f"no people in {text!r}"

    ids = {e for m in memories for e in m.entities}
    assert ids == {"samira"}, f"one person in this corpus, got {ids}"


def test_a_pronoun_is_never_reported_alongside_a_name() -> None:
    """If a name survived, the pronoun is not the thing to resolve."""
    found = mentions("Sam still works nights")
    assert found == ["Sam"]
    assert "she" not in found
