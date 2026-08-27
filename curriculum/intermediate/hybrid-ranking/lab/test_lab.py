"""Six signals, and the one that reaches what words cannot. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.eval.exam import QUESTION
from memlab.pipeline import at
from memlab.retrieve.query import slots_for
from memlab.retrieve.scoped import eligible
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

AFFINITY = _solution.AFFINITY
Intent = _solution.Intent
coverage = _solution.coverage
intent_of = _solution.intent_of
rank = _solution.rank
score_one = _solution.score_one
slot_match = _solution.slot_match
subject_match = _solution.subject_match

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def pool(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("hy") / "m.jsonl")
    ingest(store, PRIYA, at("I5"))
    return eligible(store.all(), PRIYA)


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.coverage("a", "b")


def test_the_employer_reaches_rank_two(pool) -> None:
    """12 -> 2, on signals the store already had."""
    hits = rank(QUESTION, pool, PRIYA, k=len(pool))
    place = next(i for i, h in enumerate(hits, 1) if "works at Calico" in h.memory.content)
    assert place == 2


def test_similarity_is_the_smallest_contributor(pool) -> None:
    """The correct answer barely resembles the question as text."""
    now = max((m.happened_at or m.recorded_at) for m in pool)
    employer = next(m for m in pool if "works at Calico" in m.content)
    parts = score_one(QUESTION, employer, now, intent_of(QUESTION), PRIYA,
                      slots_for(QUESTION)).parts
    assert parts["similarity"] == min(parts.values())
    assert parts["slot"] == max(parts.values())


def test_coverage_does_not_penalise_length() -> None:
    """The Jaccard bug: the long correct memory used to lose to a short wrong one."""
    q = "where does Priya work?"
    long_correct = coverage(q, "Priya works at Calico Systems")
    short_wrong = coverage(q, "Sam still works nights")
    assert long_correct > short_wrong


def test_stemming_matters() -> None:
    """`work` must match `works`, or employment queries score zero."""
    assert coverage("where does Priya work?", "Priya works at Calico Systems") > 0


def test_slot_reaches_a_fact_sharing_no_words(pool) -> None:
    gluten = next(m for m in pool if m.content == "Priya has a gluten intolerance")
    assert coverage("what should Priya not eat?", gluten.content) < 0.6
    assert slot_match(gluten, {"diet"}) == 1.0


def test_removing_the_slot_term_loses_the_gluten_fact(pool, monkeypatch) -> None:
    """The stretch, pinned -- on the COMPOUND question.

    Slot matters most where the query is diluted. Asked on its own, "what
    should Priya not eat?" reaches the gluten fact through the user's name
    alone. Asked as half of a compound question, only slot membership finds it:
    rank 5 with the term, rank 9 without.
    """
    def gluten_rank() -> int:
        hits = rank(QUESTION, pool, PRIYA, k=len(pool))
        return next(i for i, h in enumerate(hits, 1) if "has a gluten" in h.memory.content)

    assert gluten_rank() == 5
    monkeypatch.setattr(_solution, "W_SLOT", 0.0)
    assert gluten_rank() == 9


def test_subject_prefers_the_account_holder(pool) -> None:
    sam = next(m for m in pool if m.content == "Sam still works nights")
    priya = next(m for m in pool if "works at Calico" in m.content)
    assert subject_match(sam, PRIYA) == 0.0
    assert subject_match(priya, PRIYA) == 1.0


def test_intent_and_affinity() -> None:
    assert intent_of("where do I work?") == Intent.STATE
    assert intent_of("how do I run my weekly report?") == Intent.PROCEDURE
    assert intent_of("when did I change jobs?") == Intent.HISTORY
    assert AFFINITY[Intent.STATE][MemoryType.SEMANTIC] == 1.0
    assert AFFINITY[Intent.STATE][MemoryType.PROCEDURAL] == 0.0


def test_type_is_a_preference_not_a_ban() -> None:
    """A history question must still be able to reach episodes."""
    assert AFFINITY[Intent.HISTORY][MemoryType.EPISODIC] == 1.0
    assert AFFINITY[Intent.HISTORY][MemoryType.SEMANTIC] > 0
