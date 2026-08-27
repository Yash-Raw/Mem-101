"""memlab v0.1 works. Asserted -- and so are its limits."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

answer = _solution.answer
restart_check = _solution.restart_check

PRIYA = Scope(user="priya")


@pytest.fixture
def store(tmp_path):
    s = JsonlStore(tmp_path / "m.jsonl")
    ingest(s, PRIYA)
    return s


def test_stub_is_runnable(store) -> None:
    with pytest.raises(NotImplementedError):
        _lab.answer(store, PRIYA, "anything")


def test_the_loop_closes(store) -> None:
    text = answer(store, PRIYA, "what should I not eat?")
    assert "recalled beliefs" in text
    assert "meat" in text or "gluten" in text


def test_it_survives_a_restart(store) -> None:
    """The actual difference between an LLM call and a memory layer."""
    identical, rewritten = restart_check(store.path, PRIYA, "what should I not eat?")
    assert identical, "a new store object over the same file recalls identically"
    assert rewritten == 0, "and re-ingesting writes nothing"


def test_it_is_scoped_to_a_person(store) -> None:
    assert answer(store, Scope(user="someone-else"), "what should I not eat?") == ""


def test_it_recalls_a_taught_procedure(store) -> None:
    text = answer(store, PRIYA, "how do I write my weekly report?")
    assert "diff against last week" in text


def test_and_it_holds_three_people_who_are_one(store) -> None:
    """Working, and wrong. Both true at once."""
    text = answer(store, PRIYA, "who is Sam?", k=10, budget=800)
    assert sum(name in text for name in ("Sam ", "Samira", "Sammy")) >= 2, (
        "the system never had the concept that these might be one person"
    )
