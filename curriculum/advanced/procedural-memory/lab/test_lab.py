"""Order survives because the extractor refuses to split it."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.fixtures import load_gold
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

annotation = _solution.annotation
build = _solution.build
order_preserved = _solution.order_preserved
parse = _solution.parse

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("pm") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    return s.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.build(memories)


def test_two_typed_procedural_one_is_a_procedure(memories) -> None:
    assert sum(1 for m in memories if m.type is MemoryType.PROCEDURAL) == 2
    assert len(build(memories)) == 1


def test_the_order_survives_the_write_path(memories) -> None:
    gold = load_gold()["procedures"][0]
    procedure = build(memories)[0]
    assert list(procedure.steps) == gold["ordered_steps"]
    assert order_preserved(procedure, gold["ordered_steps"])


def test_the_critical_step_is_second_of_four(memories) -> None:
    """No positional heuristic finds the middle."""
    procedure = build(memories)[0]
    assert procedure.critical == "diff"
    assert procedure.position(procedure.critical) == 2
    assert len(procedure.steps) == 4


def test_the_annotation_would_parse_into_a_workflow_that_does_not_exist(
    memories,
) -> None:
    found = annotation(memories)
    assert found is not None
    assert found[0].type is MemoryType.PROCEDURAL
    assert list(parse(found[0])) == [
        "In Priya's weekly report", "the diff step matters most"
    ]


def test_nothing_links_the_annotation_to_the_procedure(memories) -> None:
    found = annotation(memories)
    assert found[0].derived_from == ()
    procedure = build(memories)[0]
    assert procedure.memory.derived_from == ()
    assert procedure.linked, "attached by content, because there is no link to follow"


def test_gold_matches_the_corpus_wording(memories) -> None:
    """The corpus says "write it up"; gold said "write up" until this lesson."""
    from memlab.fixtures import load_turns

    said = next(
        t["text"] for t in load_turns() if t["session"] == 6 and "memorise" in t["text"]
    )
    for step in load_gold()["procedures"][0]["ordered_steps"]:
        assert step.lower() in said.lower() or step in build(memories)[0].steps
