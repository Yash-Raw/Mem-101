"""Two packing policies, both no-ops. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ask, ingest
from memlab.eval.exam import QUESTION
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

pack = _solution.pack
NEEDED = ("works at Calico", "does not eat meat", "eats fish", "gluten")
PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def hits(tmp_path_factory):
    pipeline = at("I7")
    store = JsonlStore(tmp_path_factory.mktemp("pk") / "m.jsonl")
    ingest(store, PRIYA, pipeline)
    pipeline.vectors.index(store.all())
    _ctx, hits = ask(store, PRIYA, QUESTION, k=5, pipeline=pipeline)
    return hits


def complete(hits, budget, **kw) -> bool:
    out = pack(hits, budget_tokens=budget, **kw)
    return all(any(n in h.memory.content for h in out.kept) for n in NEEDED)


def test_stub_is_runnable(hits) -> None:
    with pytest.raises(NotImplementedError):
        _lab.pack(hits, budget_tokens=400)


def test_hits_know_which_question_surfaced_them(hits) -> None:
    """Attribution is what makes allocation possible."""
    assert {h.query for h in hits} == {
        "where do Priya work?", "what should Priya not eat?"
    }


def test_a_complete_answer_costs_77_tokens(hits) -> None:
    assert complete(hits, 77)
    assert not complete(hits, 70)


def test_padding_suppression_changes_nothing(hits) -> None:
    """The measured no-op this lesson is built on."""
    for budget in (80, 77, 70, 67, 60):
        assert complete(hits, budget, suppress_padding=False) == complete(
            hits, budget, suppress_padding=True
        )


def test_because_the_padding_was_already_losing(hits) -> None:
    """Demoting it moves it behind facts it was already behind."""
    scored = {h.memory.content: h.score for h in hits}
    staff = next(s for c, s in scored.items() if "staff engineer" in c)
    fish = next(s for c, s in scored.items() if "eats fish" in c)
    gluten = next(s for c, s in scored.items() if "gluten" in c)
    assert fish > staff > gluten


def test_every_question_still_gets_an_answer(hits) -> None:
    out = pack(hits, budget_tokens=60)
    assert {h.query for h in out.kept} == {h.query for h in hits}


def test_memories_are_never_truncated(hits) -> None:
    out = pack(hits, budget_tokens=45)
    originals = {h.memory.content for h in hits}
    for kept in out.kept:
        assert kept.memory.content in originals


def test_the_budget_is_respected(hits) -> None:
    for budget in (80, 60, 45, 20):
        assert pack(hits, budget_tokens=budget).used <= budget
