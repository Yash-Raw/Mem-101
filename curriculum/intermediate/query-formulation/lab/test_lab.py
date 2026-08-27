"""The query is not the last message. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.eval.exam import QUESTION
from memlab.pipeline import at
from memlab.retrieve.scoped import eligible
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

decompose = _solution.decompose
formulate = _solution.formulate
in_slots = _solution.in_slots
resolve = _solution.resolve
slots_for = _solution.slots_for

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def pool(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("qf") / "m.jsonl")
    ingest(store, PRIYA, at("I5"))
    return eligible(store.all(), PRIYA)


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.decompose("a and what b?")


def test_first_person_resolves_to_the_account_holder() -> None:
    assert resolve("where do I work?", PRIYA) == "where do Priya work?"


def test_a_compound_question_becomes_two() -> None:
    assert formulate(QUESTION, PRIYA) == [
        "where do Priya work?",
        "what should Priya not eat?",
    ]


def test_a_single_question_is_left_alone() -> None:
    assert decompose("where do I work?") == ["where do I work?"]


def test_listing_conjunctions_are_not_split() -> None:
    """Splitting on any `and` would turn one question into two bad ones."""
    assert len(decompose("does Priya eat fish and meat?")) == 1


def test_questions_map_to_slots() -> None:
    assert slots_for("where do Priya work?") == {"employer"}
    assert slots_for("what should Priya not eat?") == {"diet"}


def test_the_slot_finds_a_fact_sharing_no_words(pool) -> None:
    """The point of the whole mechanism."""
    found = in_slots(pool, {"diet"})
    contents = {m.content for m in found}
    assert "Priya has a gluten intolerance" in contents
    assert len(found) == 5

    gluten = "Priya has a gluten intolerance".lower().split()
    assert not (set(gluten) & set(QUESTION.lower().split()))


def test_no_slots_means_no_candidates(pool) -> None:
    """Degrades to similarity rather than returning everything."""
    assert in_slots(pool, set()) == []
