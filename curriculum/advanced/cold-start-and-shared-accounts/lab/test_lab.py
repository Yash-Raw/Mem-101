"""Complete two turns before correct, and one field between two people."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.fixtures import load_turns
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope
from memlab.user.apply import apply
from memlab.user.model import build

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

answerable = _solution.answerable
growth = _solution.growth
merged = _solution.merged

PRIYA = Scope(user="priya")
QUESTION = "where do I work and what should I not eat?"
NEEDED = ("Calico", "does not eat meat", "eats fish", "gluten")


@pytest.fixture(scope="module")
def walked(tmp_path_factory):
    """Snapshots and milestones from one turn-by-turn replay."""
    pipeline = at("A3")
    store = JsonlStore(tmp_path_factory.mktemp("cs") / "m.jsonl")
    store.clear()
    snapshots, marks = [], {}
    turns = [t for t in load_turns(user_only=True) if t["session"] < 14]
    for i, turn in enumerate(turns, 1):
        memories = pipeline.extract(turn, PRIYA)
        if pipeline.resolve is not None:
            memories = pipeline.resolve(memories, store.all())
        store.add(memories)
        store.replace(pipeline.consolidate(store.all()))
        model = build(store.all(), PRIYA)
        if i in (1, 3, 8, 12, 20, 24):
            snapshots.append((i, store.all()))
        if "reached" not in marks and apply(model, QUESTION, PRIYA).asked:
            marks["reached"] = i
        if "complete" not in marks and len(model.attributes) == 6:
            marks["complete"] = i
        if "answers" not in marks and answerable(model, QUESTION, PRIYA, NEEDED):
            marks["answers"] = i
    return snapshots, marks, len(turns)


def test_stub_is_runnable(walked) -> None:
    snapshots, _marks, _n = walked
    with pytest.raises(NotImplementedError):
        _lab.growth(snapshots, PRIYA)


def test_half_the_model_exists_after_three_turns(walked) -> None:
    snapshots, _marks, _n = walked
    curve = {c.turn: c.size for c in growth(snapshots, PRIYA)}
    assert curve == {1: 1, 3: 3, 8: 4, 12: 5, 20: 6, 24: 6}


def test_complete_two_turns_before_correct(walked) -> None:
    """A gate on attribute count goes green while a needed fact is missing."""
    _snapshots, marks, _n = walked
    assert marks["reached"] == 1
    assert marks["complete"] == 20
    assert marks["answers"] == 22
    assert marks["answers"] - marks["complete"] == 2


def test_the_missing_fact_is_the_gluten_intolerance(walked) -> None:
    snapshots, _marks, _n = walked
    at_20 = next(memories for turn, memories in snapshots if turn == 20)
    model = build(at_20, PRIYA)
    assert len(model.attributes) == 6
    text = " ".join(v for a in apply(model, QUESTION, PRIYA).asked for v in a.values)
    assert "gluten" not in text
    assert not answerable(model, QUESTION, PRIYA, NEEDED)


def test_a_partial_model_answers_less_not_wrongly(walked) -> None:
    snapshots, _marks, _n = walked
    at_3 = build(next(m for t, m in snapshots if t == 3), PRIYA)
    applied = apply(at_3, QUESTION, PRIYA)
    assert {a.slot for a in applied.asked} <= {"diet", "employer"}
    assert all(a.beliefs for a in applied.asked), "no empty guesses"


def test_stripping_entities_merges_two_people(tmp_path) -> None:
    store = JsonlStore(tmp_path / "shared.jsonl")
    store.clear()
    ingest(store, PRIYA, at("A3"))
    intact = build(store.all(), PRIYA)
    shared = merged(store.all(), PRIYA)

    assert len(intact.attributes) == 6
    assert len(shared.attributes) == 7
    gained = set(shared.attributes) - set(intact.attributes)
    assert gained == {"occupation_other"}
    contents = [b.content for b in shared.attributes["occupation_other"].beliefs]
    assert "Samira is a charge nurse" in contents
    assert intact.third_party and not shared.third_party
