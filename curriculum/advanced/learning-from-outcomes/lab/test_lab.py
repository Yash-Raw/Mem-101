"""The conclusion survived; the evidence did not."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.fixtures import load_turns
from memlab.pipeline import at
from memlab.procedural.steps import build
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

attach = _solution.attach
extract = _solution.extract
recorded = _solution.recorded

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("lo") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    memories = s.all()
    return memories, build(memories)[0]


@pytest.fixture(scope="module")
def lessons():
    out = []
    for turn in load_turns():
        if turn["session"] < 14:
            out += extract(turn["text"], f"s{turn['session']}:{turn['ts']}")
    return out


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.extract("If you skip it the numbers look fine.")


def test_one_lesson_in_twenty_four_turns(lessons) -> None:
    assert len(lessons) == 1
    assert lessons[0].consequence == "the numbers look fine and they aren't"


def test_the_consequence_is_not_in_the_store(env, lessons) -> None:
    """The store believes the step matters and cannot say why."""
    memories, _procedure = env
    assert not recorded(memories, lessons[0])
    for probe in ("numbers look fine", "skip", "aren'"):
        assert not any(probe in m.content for m in memories)


def test_the_conclusion_did_survive(env) -> None:
    memories, _p = env
    assert any("the diff step matters most" in m.content for m in memories)


def test_the_pronoun_binds_only_with_the_annotation(env, lessons) -> None:
    _memories, procedure = env
    bound = attach(lessons[0], procedure.steps, procedure.critical)
    assert bound.trigger == "it"
    assert bound.step == "diff against last week"
    assert bound.attached

    orphaned = attach(lessons[0], procedure.steps, None)
    assert orphaned.step is None, "without the annotation there is no 'it' to resolve"


def test_reading_the_store_finds_nothing(env, lessons) -> None:
    """A feature over the store concludes the user never explains themselves."""
    memories, _p = env
    from_store = []
    for memory in memories:
        from_store += extract(memory.content, memory.provenance.source_id)
    assert from_store == []
    assert len(lessons) == 1


def test_the_source_turn_contains_both_halves(lessons) -> None:
    said = next(
        t["text"] for t in load_turns()
        if t["session"] == 6 and "matters most" in t["text"]
    )
    assert "the diff step matters most" in said.lower()
    assert lessons[0].consequence in said
