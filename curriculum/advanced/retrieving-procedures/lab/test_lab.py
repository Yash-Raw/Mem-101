"""A different index, a different trigger, a different injection point."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ask, ingest
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

is_procedural = _solution.is_procedural
render = _solution.render
search = _solution.search

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    pipeline = at("A3")
    s = JsonlStore(tmp_path_factory.mktemp("rp") / "m.jsonl")
    ingest(s, PRIYA, pipeline)
    pipeline.vectors.index(s.all())
    return s, pipeline, s.all()


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.is_procedural("how do I do the weekly report?")


@pytest.mark.parametrize(
    "question,expected",
    [
        ("how do I do the weekly report?", True),
        ("what are the steps for the weekly report", True),
        ("where do I work?", False),
        ("what did I say about the Spark job?", False),
    ],
)
def test_routing(question, expected) -> None:
    assert is_procedural(question) is expected


def test_the_fact_path_never_finds_the_procedure(built) -> None:
    store, pipeline, _ms = built
    hits = ask(store, PRIYA, "how do I do the weekly report?", k=5, pipeline=pipeline)[1]
    assert not any(h.memory.type is MemoryType.PROCEDURAL for h in hits)


def test_and_returns_the_footnote_when_it_finds_anything(built) -> None:
    store, pipeline, _ms = built
    hits = ask(
        store, PRIYA, "what are the steps for the weekly report", k=5, pipeline=pipeline
    )[1]
    assert hits[0].memory.type is MemoryType.PROCEDURAL
    assert hits[0].memory.content == (
        "In Priya's weekly report, the diff step matters most"
    )


def test_the_procedural_path_finds_the_workflow(built) -> None:
    _s, _p, memories = built
    for question in ("how do I do the weekly report?",
                     "what are the steps for the weekly report"):
        found = search(question, memories)
        assert len(found) == 1
        assert len(found[0].steps) == 4


def test_a_recall_question_is_not_routed_here(built) -> None:
    _s, _p, memories = built
    assert search("where do I work?", memories) == []
    assert search("what did I say about the Spark job?", memories) == []


def test_the_workflow_renders_whole_and_numbered(built) -> None:
    _s, _p, memories = built
    text = render(search("how do I do the weekly report?", memories)[0])
    lines = text.splitlines()
    assert len(lines) == 5
    assert lines[0].startswith("1. pull pipeline metrics")
    assert lines[3].startswith("4. write it up")
    assert lines[4] == "(step 2 matters most)"


def test_the_annotation_is_not_a_candidate(built) -> None:
    """A5.1 established it is not a procedure; the index inherits that."""
    _s, _p, memories = built
    found = search("what are the steps for the weekly report", memories)
    assert "matters most" not in found[0].procedure.memory.content
