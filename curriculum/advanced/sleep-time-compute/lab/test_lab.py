"""The window is the cost, and the gate that closes it is already computed."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import _agent_memories
from memlab.evolve.conflict import slot_of
from memlab.fixtures import load_turns
from memlab.pipeline import at
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Gate = _solution.Gate
Schedule = _solution.Schedule

PRIYA = Scope(user="priya")
STALE = "data engineer at Northwind"


def _stale(store):
    return sum(1 for m in store.all() if m.is_live and STALE in m.content)


@pytest.fixture(scope="module")
def harness(tmp_path_factory):
    """Turn-by-turn replay, with a per-turn-consolidated reference to diff."""
    import memlab.evolve.dedupe as dedupe_mod
    from memlab.store.jsonl import JsonlStore

    pipeline = at("A2")
    turns = [t for t in load_turns(user_only=True) if t["session"] < 14]
    root = tmp_path_factory.mktemp("sleep")

    eager = JsonlStore(root / "ref.jsonl")
    reference = []
    for turn in turns:
        memories = pipeline.extract(turn, PRIYA)
        if pipeline.resolve is not None:
            memories = pipeline.resolve(memories, eager.all())
        eager.add(memories)
        eager.replace(pipeline.consolidate(eager.all()))
        reference.append(_stale(eager))

    def walk(schedule, post_write_store=False):
        counts = {"embed": 0, "cosine": 0}
        embed, cosine = dedupe_mod.embed_text, dedupe_mod.cosine
        dedupe_mod.embed_text = lambda *a, **k: (
            counts.__setitem__("embed", counts["embed"] + 1), embed(*a, **k)
        )[1]
        dedupe_mod.cosine = lambda *a, **k: (
            counts.__setitem__("cosine", counts["cosine"] + 1), cosine(*a, **k)
        )[1]
        store = JsonlStore(root / "walk.jsonl")
        store.clear()
        runs, wrong = 0, 0
        for i, turn in enumerate(turns):
            before = store.all()
            memories = pipeline.extract(turn, PRIYA)
            if pipeline.resolve is not None:
                memories = pipeline.resolve(memories, before)
            store.add(memories)
            seen = store.all() if post_write_store else before
            if schedule.needs_inline(memories, seen):
                store.replace(pipeline.consolidate(store.all()))
                runs += 1
            if _stale(store) != reference[i]:
                wrong += 1
        store.add(_agent_memories(PRIYA))
        store.replace(pipeline.consolidate(store.all()))
        runs += 1
        dedupe_mod.embed_text, dedupe_mod.cosine = embed, cosine
        return {
            "runs": runs,
            "embed": counts["embed"],
            "cosine": counts["cosine"],
            "wrong": wrong,
            "live": sum(m.is_live for m in store.all()),
        }

    return walk


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.Schedule.never().needs_inline([], [])


def test_deferring_everything_is_wrong_for_eleven_turns(harness) -> None:
    r = harness(Schedule.never())
    assert (r["runs"], r["embed"], r["cosine"]) == (1, 38, 282)
    assert r["wrong"] == 11


def test_consolidating_every_turn_costs_thirteen_times_the_embeddings(harness) -> None:
    r = harness(Schedule.always())
    assert (r["runs"], r["embed"], r["cosine"]) == (25, 503, 1630)
    assert r["wrong"] == 0


def test_the_ratio_is_thirteen_to_one(harness) -> None:
    """503 embeddings against 38, for the identical store."""
    deferred, eager = harness(Schedule.never()), harness(Schedule.always())
    assert round(eager["embed"] / deferred["embed"]) == 13
    assert deferred["live"] == eager["live"]


def test_the_type_gate_barely_helps(harness) -> None:
    """24 of 35 memories are semantic; the filter is nearly constant True."""
    r = harness(Schedule.by_type())
    assert (r["runs"], r["embed"], r["cosine"]) == (19, 365, 1199)
    assert r["wrong"] == 0


def test_the_contested_slot_gate_is_the_one_that_works(harness) -> None:
    """44% of the runs, 56% of the embeddings, zero wrong turns."""
    r = harness(Schedule.default())
    assert (r["runs"], r["embed"], r["cosine"]) == (11, 281, 1011)
    assert r["wrong"] == 0


def test_every_gate_converges_to_the_same_store(harness) -> None:
    """Order-independence is what makes any of this safe."""
    for schedule in (
        Schedule.never(), Schedule.by_type(), Schedule.default(), Schedule.always()
    ):
        assert harness(schedule)["live"] == 30


def test_the_type_that_matters_is_the_type_that_dominates() -> None:
    pipeline = at("A2")
    turns = [t for t in load_turns(user_only=True) if t["session"] < 14]
    written = [(t, pipeline.extract(t, PRIYA)) for t in turns]
    memories = [m for _t, ms in written for m in ms]
    assert sum(1 for m in memories if m.type is MemoryType.SEMANTIC) == 24
    assert len(memories) == 35
    assert sum(
        1 for _t, ms in written if any(m.type is MemoryType.SEMANTIC for m in ms)
    ) == 18


def test_passing_the_post_write_store_inflates_the_gate(harness) -> None:
    """11 -> 18 runs, same output. Not quite `always`, and that is worse.

    A gate that degraded all the way to 25 would at least look like `always`
    in a cost graph. 18 looks like a working gate that is simply less
    effective than the measurement said -- which is not a difference anyone
    notices without the pre-turn/post-turn comparison.
    """
    degraded = harness(Schedule.default(), post_write_store=True)
    correct = harness(Schedule.default())
    assert (correct["runs"], degraded["runs"]) == (11, 18)
    assert degraded["wrong"] == correct["wrong"] == 0
    assert degraded["live"] == correct["live"] == 30


def test_the_gate_needs_no_computation_of_its_own(harness) -> None:
    """It reads `slot_of`, which the write path computes a moment later."""
    pipeline = at("A2")
    employer_turns = [
        t["session"]
        for t in load_turns(user_only=True)
        if t["session"] < 14
        and any(slot_of(m) == "employer" for m in pipeline.extract(t, PRIYA))
    ]
    assert employer_turns == [1, 8, 9], "claimed once, then contested twice"
    assert Schedule.default().gate is Gate.CONTESTED
