"""Same context, same cost, and one sentence retrieval cannot say."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.assemble.simple import estimate_tokens
from memlab.assemble.value import COMPACT_HEADER
from memlab.eval.exam import QUESTION, exam_from_context
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope
from memlab.user.model import build

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

INSTRUCTIONS = _solution.INSTRUCTIONS
Mode = _solution.Mode
apply = _solution.apply
asked_slots = _solution.asked_slots
disclosure = _solution.disclosure
mode = _solution.mode

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    pipeline = at("A3")
    s = JsonlStore(tmp_path_factory.mktemp("am") / "m.jsonl")
    ingest(s, PRIYA, pipeline)
    return s.all(), pipeline, build(s.all(), PRIYA)


def test_stub_is_runnable(built) -> None:
    _memories, _p, model = built
    with pytest.raises(NotImplementedError):
        _lab.apply(model, QUESTION, PRIYA)


@pytest.mark.parametrize(
    "question,asked,silent,held",
    [
        ("where do I work and what should I not eat?", 2, 1, 3),
        ("what should I not eat?", 1, 1, 4),
        ("where do I work?", 1, 1, 4),
        ("what am I like to talk to?", 0, 1, 5),
    ],
)
def test_the_split(built, question, asked, silent, held) -> None:
    _memories, _p, model = built
    applied = apply(model, question, PRIYA)
    assert (len(applied.asked), len(applied.instructions), len(applied.withheld)) == (
        asked, silent, held
    )


def test_the_address_is_never_volunteered(built) -> None:
    _memories, _p, model = built
    for question in ("what should I not eat?", "what am I like to talk to?"):
        applied = apply(model, question, PRIYA)
        assert "residence" not in {a.slot for a in applied.asked}
        assert "residence" in {a.slot for a in applied.withheld}


def test_the_preference_is_always_applied_and_never_stated(built) -> None:
    """Nobody will ask about it, and applying it is the point."""
    _memories, _p, model = built
    for question in ("what should I not eat?", "what am I like to talk to?"):
        applied = apply(model, question, PRIYA)
        assert [a.slot for a in applied.instructions] == ["response_style"]
    assert mode("response_style") is Mode.INSTRUCTION
    assert mode("residence") is Mode.ANSWER


def test_restraint_is_cheaper(built) -> None:
    _memories, _p, model = built
    everything = estimate_tokens(
        " ".join(v for a in model.attributes.values() for v in a.values)
    )
    assert everything == 75
    costs = []
    for question in (
        "where do I work and what should I not eat?",
        "what should I not eat?",
        "where do I work?",
        "what am I like to talk to?",
    ):
        applied = apply(model, question, PRIYA)
        costs.append(estimate_tokens(" ".join(
            v for a in applied.asked + applied.instructions for v in a.values
        )))
    assert costs == [44, 30, 21, 7]
    assert all(c < everything for c in costs)


def test_against_retrieval_it_is_a_tie(built) -> None:
    """Both arrive at the same six memories, by different routes."""
    memories, pipeline, model = built
    applied = apply(model, QUESTION, PRIYA)
    beliefs = [m for a in applied.asked for m in a.beliefs]
    assert len(beliefs) == 6
    context = COMPACT_HEADER + "\n" + "\n".join(f"- {m.content}" for m in beliefs)
    lowest = next(
        b for b in range(30, 90)
        if exam_from_context(memories, PRIYA, k=5, pipeline=pipeline,
                             budget=b).is_correct
    )
    assert estimate_tokens(context) == lowest == 51


def test_the_context_carries_all_four_required_facts(built) -> None:
    _memories, _p, model = built
    beliefs = [m for a in apply(model, QUESTION, PRIYA).asked for m in a.beliefs]
    text = " ".join(m.content for m in beliefs)
    for fact in ("Calico", "does not eat meat", "eats fish", "gluten"):
        assert fact in text


def test_disclosure_reports_what_was_withheld(built) -> None:
    """The line retrieval cannot produce."""
    _memories, _p, model = built
    lines = disclosure(apply(model, QUESTION, PRIYA))
    assert sum(1 for line in lines if line.startswith("used:")) == 2
    assert "applied silently: response_style" in lines
    assert "held, not used: residence" in lines
    assert len(lines) == 6


def test_the_model_and_the_retriever_read_a_question_the_same_way(built) -> None:
    from memlab.retrieve.query import formulate, slots_for

    reached = set()
    for sub in formulate(QUESTION, PRIYA):
        reached |= slots_for(sub)
    assert asked_slots(QUESTION, PRIYA) == reached == {"diet", "employer"}


def test_instructions_is_short_and_explicit() -> None:
    assert INSTRUCTIONS == frozenset({"response_style"})
