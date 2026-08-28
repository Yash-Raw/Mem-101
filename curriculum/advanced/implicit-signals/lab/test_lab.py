"""The user names the wrong belief out loud, and nothing is listening."""
from __future__ import annotations

from dataclasses import replace as dc_replace

import pytest
from memlab import labkit
from memlab.app.chat import _agent_memories, ingest
from memlab.fixtures import load_turns
from memlab.pipeline import at
from memlab.sleep.schedule import Schedule
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

attribute = _solution.attribute
corrections = _solution.corrections
used = _solution.used

PRIYA = Scope(user="priya")
STALE = "data engineer at Northwind"


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("is") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    return s.all()


@pytest.fixture(scope="module")
def turns():
    return [t for t in load_turns() if t["session"] < 14]


def test_stub_is_runnable(turns) -> None:
    with pytest.raises(NotImplementedError):
        _lab.corrections(turns)


def test_nothing_records_having_been_used(memories) -> None:
    assert used(memories) == 0
    assert len(memories) == 37


def test_exactly_one_correction(turns) -> None:
    found = corrections(turns)
    assert len(found) == 1
    assert found[0].session == 9
    assert "remember?" in found[0].user_replied


def test_it_is_attributed_to_the_right_belief(turns, memories) -> None:
    found = attribute(corrections(turns)[0], memories)
    assert found.attributed
    assert found.target.content == "Priya is a data engineer at Northwind Labs"


def test_a_correction_needs_an_assistant_turn_before_it(turns) -> None:
    """Unprompted, it is the user changing their mind -- an ordinary write."""
    user_only = [t for t in turns if t["role"] == "user"]
    assert corrections(user_only) == []


def test_the_narrow_pattern_ignores_still_no_meat(turns) -> None:
    """The stretch, inverted: a broad pattern retires a true belief."""
    diet_turn = next(t for t in turns if "Still no meat" in t.get("text", ""))
    assert not any(c.user_replied == diet_turn["text"] for c in corrections(turns))


def _reference(pipeline, user_turns, tmp_path):
    eager = JsonlStore(tmp_path / "ref.jsonl")
    eager.clear()
    out = []
    for turn in user_turns:
        memories = pipeline.extract(turn, PRIYA)
        if pipeline.resolve is not None:
            memories = pipeline.resolve(memories, eager.all())
        eager.add(memories)
        eager.replace(pipeline.consolidate(eager.all()))
        out.append(sum(1 for m in eager.all() if m.is_live and STALE in m.content))
    return out


def _walk(pipeline, user_turns, every_turn, reference, schedule, act, tmp_path):
    store = JsonlStore(tmp_path / "walk.jsonl")
    store.clear()
    runs, wrong, acted = 0, 0, set()
    for i, turn in enumerate(user_turns):
        before = store.all()
        memories = pipeline.extract(turn, PRIYA)
        if pipeline.resolve is not None:
            memories = pipeline.resolve(memories, before)
        store.add(memories)
        if schedule.needs_inline(memories, before):
            store.replace(pipeline.consolidate(store.all()))
            runs += 1
        if act:
            # By timestamp, not by session: session 9 has two user turns and
            # the correction is the second, so filtering by session applies
            # the signal one turn before the user gives it.
            so_far = [t for t in every_turn if t["ts"] <= turn["ts"]]
            for correction in corrections(so_far):
                if correction.session in acted:
                    continue
                found = attribute(correction, store.all())
                if found.target and found.target.is_live:
                    acted.add(correction.session)
                    store.replace([
                        dc_replace(m, invalid_at=m.recorded_at,
                                   superseded_by="correction")
                        if m.id == found.target.id else m
                        for m in store.all()
                    ])
        if sum(1 for m in store.all()
               if m.is_live and STALE in m.content) != reference[i]:
            wrong += 1
    store.add(_agent_memories(PRIYA))
    store.replace(pipeline.consolidate(store.all()))
    return wrong, sum(m.is_live for m in store.all())


def test_corrections_take_eleven_wrong_turns_to_three(turns, tmp_path) -> None:
    pipeline = at("A3")
    user_turns = [t for t in load_turns(user_only=True) if t["session"] < 14]
    reference = _reference(pipeline, user_turns, tmp_path)

    deferred = _walk(pipeline, user_turns, turns, reference,
                     Schedule.never(), False, tmp_path)
    gated = _walk(pipeline, user_turns, turns, reference,
                  Schedule.default(), False, tmp_path)
    signalled = _walk(pipeline, user_turns, turns, reference,
                      Schedule.never(), True, tmp_path)

    assert deferred[0] == 11
    assert gated[0] == 0
    assert signalled[0] == 3
    assert deferred[1] == gated[1] == signalled[1] == 30


def test_the_three_that_remain_are_before_the_complaint(turns) -> None:
    """Turns 14-16: she has announced the move, and not yet objected."""
    user_turns = [t for t in load_turns(user_only=True) if t["session"] < 14]
    announcement = next(
        i for i, t in enumerate(user_turns, 1) if "leaving Northwind" in t["text"]
    )
    complaint = next(
        i for i, t in enumerate(user_turns, 1) if "remember?" in t["text"]
    )
    assert (announcement, complaint) == (14, 17)
    assert complaint - announcement == 3
    assert list(range(announcement, complaint)) == [14, 15, 16], (
        "the window in which she has told you and the store has not caught up"
    )
