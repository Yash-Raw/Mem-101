"""memlab v0.1's failures, pinned.

These tests assert that the Beginner system is BROKEN in seven specific ways.
They are the baseline the whole rest of the course is measured against, and the
numbers here are quoted in `watching-it-fail`. When Level 2 fixes a failure, the
corresponding test moves to the intermediate suite and flips its expectation.
"""
from __future__ import annotations

import pytest
from memlab.app.chat import ingest
from memlab.retrieve.embedding import EmbeddingRetriever
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

QUESTION = "where do I work and what should I not eat?"


@pytest.fixture(scope="module")
def store(tmp_path_factory) -> JsonlStore:
    s = JsonlStore(tmp_path_factory.mktemp("memlab") / "memories.jsonl")
    ingest(s, Scope(user="priya"))
    return s


@pytest.fixture(scope="module")
def ranked(store):
    return EmbeddingRetriever().search(QUESTION, store.all(), Scope(user="priya"), k=1000)


def rank_of(ranked, needle: str) -> int | None:
    return next((i for i, h in enumerate(ranked, 1) if needle in h.memory.content), None)


def test_the_loop_actually_closes(store) -> None:
    """Before cataloguing failures: it genuinely works. 25 turns in, memories out."""
    assert len(store.all()) == 36
    assert {m.type for m in store.all()} == {
        MemoryType.SEMANTIC, MemoryType.EPISODIC, MemoryType.PROCEDURAL
    }


def test_it_survives_restart(store) -> None:
    """The whole point of persistence: a fresh object, same memories."""
    assert len(JsonlStore(store.path).all()) == 36


# --- failure 1: no supersession -------------------------------------------
def test_stale_employer_outranks_current(ranked) -> None:
    assert rank_of(ranked, "data engineer at Northwind Labs") < rank_of(ranked, "Calico Systems")


def test_the_cleanest_true_answer_ranks_dead_last(ranked) -> None:
    """"Priya is at Calico now" is the exact answer. It ranks 35th of 36."""
    assert rank_of(ranked, "at Calico now") >= len(ranked) - 1


# --- failure 2: contradictions accumulate ----------------------------------
def test_both_sides_of_a_contradiction_stay_live(store) -> None:
    live = [m.content for m in store.live()]
    assert "Priya does not drink coffee" in live
    assert "Priya drinks three coffees a day" in live
    assert all(m.superseded_by is None for m in store.all()), "nothing retires anything"


def test_both_preferences_stay_live_and_rank_adjacently(ranked) -> None:
    """Worse than being wrong: it recalls both, one rank apart."""
    assert abs(rank_of(ranked, "shorter answers") - rank_of(ranked, "detailed explanations")) == 1


# --- failure 3: a refinement is not a contradiction, and neither is detected -
def test_vegetarian_survives_the_pescatarian_update(store) -> None:
    live = [m.content for m in store.live()]
    assert "Priya is vegetarian" in live and "Priya eats fish" in live


# --- failure 4: entity fragmentation ---------------------------------------
def test_one_person_becomes_three(store) -> None:
    text = " ".join(m.content for m in store.all())
    assert "Sam " in text or "Sam's" in text
    assert "Samira" in text
    assert "Sammy" in text  # three surface forms, three separate "people"


def test_an_unresolved_pronoun_is_stored_as_a_fact(store) -> None:
    assert any(m.content.startswith("She works nights") for m in store.all())


# --- failure 5: PII walks straight in --------------------------------------
def test_pii_is_stored_with_no_gate(store) -> None:
    text = " ".join(m.content for m in store.all())
    assert "47 Halloway Road" in text and "07700 900412" in text


def test_the_deletion_request_is_filed_instead_of_honoured(store) -> None:
    """Priya asked for the address to be forgotten. It became a memory ABOUT asking."""
    contents = [m.content for m in store.all()]
    assert "Priya asked to forget her old address" in contents
    assert any("47 Halloway Road" in c for c in contents), "and the address is still there"


# --- failure 6: events never become states ---------------------------------
def test_the_job_change_was_stored_as_events_not_a_fact(store) -> None:
    """The root cause of failure 1. No memory says `employer = Calico Systems`."""
    employer_facts = [
        m for m in store.all()
        if m.type is MemoryType.SEMANTIC and "Calico" in m.content and "starting" not in m.content
    ]
    assert [m.content for m in employer_facts] == ["Priya is at Calico now"], (
        "the only semantic form is a vague one that mentions no employer keyword"
    )


# --- failure 7: unbounded growth, no salience ------------------------------
def test_every_memory_has_identical_salience(store) -> None:
    """Nothing is more important than anything else, so nothing can be forgotten."""
    assert {m.salience for m in store.all()} == {0.5}
    assert {m.access_count for m in store.all()} == {0}


def test_top_k_is_mostly_noise(store) -> None:
    """At the default k=5, the employer does not appear at all."""
    hits = EmbeddingRetriever().search(QUESTION, store.all(), Scope(user="priya"), k=5)
    recalled = " ".join(h.memory.content for h in hits)
    assert "Calico" not in recalled and "Northwind" not in recalled
