"""Six answers from the record, three that need a read-time write."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.fixtures import load_turns
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

diff = _solution.diff
explain = _solution.explain
unanswerable = _solution.unanswerable

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("mo") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    return s.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.explain(memories[0], memories)


def test_a_belief_explains_itself_with_no_log(memories) -> None:
    found = next(m for m in memories if "works at Calico" in m.content)
    lines = explain(found, memories).lines
    joined = "\n".join(lines)
    assert "s8:2025-12-08" in joined
    assert "speaker   user" in joined
    assert "true      2025-12-08 .. open" in joined


def test_a_retired_belief_names_what_replaced_it(memories) -> None:
    """The chain is walkable because nothing on it was destroyed."""
    found = next(m for m in memories if "data engineer at Northwind" in m.content)
    explanation = explain(found, memories)
    assert explanation.replaced_by is not None
    assert "staff engineer" in explanation.replaced_by.content


def test_the_supersession_is_not_the_one_you_would_assume(memories) -> None:
    """Both arrived in session 8; arbitration compared the pair it was given."""
    found = next(m for m in memories if "data engineer at Northwind" in m.content)
    replaced_by = explain(found, memories).replaced_by
    assert "Calico" not in replaced_by.content
    assert replaced_by.provenance.source_id.startswith("s8:")


def test_nothing_is_ever_removed_by_a_write(tmp_path) -> None:
    """The invariant worth alerting on."""
    pipeline = at("A3")
    walk = JsonlStore(tmp_path / "walk.jsonl")
    walk.clear()
    removals = 0
    for turn in (t for t in load_turns(user_only=True) if t["session"] < 14):
        before = walk.all()
        written = pipeline.extract(turn, PRIYA)
        if pipeline.resolve is not None:
            written = pipeline.resolve(written, before)
        walk.add(written)
        walk.replace(pipeline.consolidate(walk.all()))
        removals += diff(before, walk.all())["removed"]
    assert removals == 0


def test_a_deletion_shows_up_as_a_removal(memories) -> None:
    from memlab.privacy.delete import purge

    target = next(m for m in memories if "Halloway" in m.content)
    assert diff(memories, purge(target, memories)) == {
        "added": 0, "removed": 1, "retired": 0
    }


def test_access_count_was_designed_for_this_and_never_written(memories) -> None:
    assert sum(1 for m in memories if m.access_count) == 0
    assert all(hasattr(m, "access_count") for m in memories)


def test_three_questions_need_a_read_time_write() -> None:
    questions = unanswerable()
    assert len(questions) == 3
    assert all(q.endswith("?") for q in questions)
    assert any("context" in q for q in questions)


def test_derivation_is_followed_both_ways(memories) -> None:
    derived = next(m for m in memories if m.derived_from)
    forward = explain(derived, memories)
    assert forward.sources
    backward = explain(forward.sources[0], memories)
    assert derived.id in {m.id for m in backward.derived}
