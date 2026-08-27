"""Most turns are not questions. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.fixtures import load_turns

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

decide = _solution.decide
should_retrieve = _solution.should_retrieve

TURNS = load_turns(user_only=True)


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.decide("anything")


def test_three_of_twenty_five_turns_retrieve() -> None:
    retrieving = [t for t in TURNS if should_retrieve(t["text"])]
    assert (len(retrieving), len(TURNS)) == (3, 25)


def test_they_are_the_right_three() -> None:
    sessions = sorted(t["session"] for t in TURNS if should_retrieve(t["text"]))
    assert sessions == [3, 13, 14]


def test_an_instruction_is_not_a_question() -> None:
    text = "Also can you keep answers shorter from now on? I don't have time for essays anymore."
    d = decide(text)
    assert not d.retrieve and "instruction" in d.reason


def test_a_correction_is_not_a_question() -> None:
    """Retrieving here is how the assistant argues with the user."""
    text = "I left Northwind last month, remember? I'm at Calico now."
    d = decide(text)
    assert not d.retrieve and "correction" in d.reason


def test_the_exam_question_retrieves() -> None:
    d = decide("Quick one: where do I work and what should I not eat?")
    assert d.retrieve


def test_statements_do_not_retrieve() -> None:
    assert not should_retrieve("I don't drink coffee, never have. Tea only.")
    assert not should_retrieve("We moved. New place is 47 Halloway Road, Bristol.")


def test_where_remember_is_classified_is_the_policy() -> None:
    """"remember?" is a CORRECTION cue, not a RECALL cue -- deliberately.

    The word is genuinely ambiguous: "do you remember X?" asks the store, and
    "X, remember?" tells it. Which list it lives in decides whether the
    assistant recalls a stale fact at the exact moment the user is correcting
    it. Both readings are in the cue tables, split by phrasing.
    """
    assert "remember?" in _solution.CORRECTION
    assert "do you remember" in _solution.RECALL

    correcting = "I left Northwind last month, remember? I'm at Calico now."
    asking = "do you remember where I work?"
    assert not decide(correcting).retrieve
    assert decide(asking).retrieve
