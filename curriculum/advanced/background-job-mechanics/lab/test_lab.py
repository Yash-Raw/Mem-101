"""A job that writes back only what it read."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import _agent_memories
from memlab.fixtures import load_turns
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

merge = _solution.merge
read = _solution.read
run = _solution.run
write_back = _solution.write_back

PRIYA = Scope(user="priya")
SESSION_8 = 13


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    pipeline = at("A2")
    turns = [t for t in load_turns(user_only=True) if t["session"] < 14]
    return pipeline, turns, tmp_path_factory.mktemp("job")


def _grown_to(pipeline, turns, k, path):
    store = JsonlStore(path)
    store.clear()
    for turn in turns[:k]:
        memories = pipeline.extract(turn, PRIYA)
        if pipeline.resolve is not None:
            memories = pipeline.resolve(memories, store.all())
        store.add(memories)
    store.replace(pipeline.consolidate(store.all()))
    return store


def _race(pipeline, turns, k, guarded, root):
    store = _grown_to(pipeline, turns, k, root / "race.jsonl")
    snapshot = read(store)
    late = pipeline.extract(turns[k], PRIYA)
    if pipeline.resolve is not None:
        late = pipeline.resolve(late, store.all())
    store.add(late)
    computed = pipeline.consolidate(list(snapshot.memories))
    if guarded:
        write_back(store, snapshot, computed)
    else:
        store.replace(computed)
    surviving = {m.id for m in store.all()}
    return store, [m for m in late if m.id not in surviving]


def test_stub_is_runnable(env) -> None:
    pipeline, turns, root = env
    store = _grown_to(pipeline, turns, 3, root / "stub.jsonl")
    with pytest.raises(NotImplementedError):
        _lab.read(store)


def test_replace_destroys_thirty_three_memories(env) -> None:
    pipeline, turns, root = env
    total = sum(
        len(_race(pipeline, turns, k, False, root)[1]) for k in range(1, len(turns))
    )
    assert total == 33


def test_the_merge_destroys_none(env) -> None:
    pipeline, turns, root = env
    total = sum(
        len(_race(pipeline, turns, k, True, root)[1]) for k in range(1, len(turns))
    )
    assert total == 0


def test_the_worst_turn_loses_the_whole_job_change(env) -> None:
    """Session 8: the announcement, all four memories."""
    pipeline, turns, root = env
    _store, lost = _race(pipeline, turns, SESSION_8, False, root)
    assert len(lost) == 4
    assert any("leaving Northwind Labs" in m.content for m in lost)
    assert any("works at Calico Systems" in m.content for m in lost)


def test_and_the_guard_keeps_all_four(env) -> None:
    pipeline, turns, root = env
    _store, lost = _race(pipeline, turns, SESSION_8, True, root)
    assert lost == []


def _build(pipeline, turns, root, raced):
    store = JsonlStore(root / f"build-{raced}.jsonl")
    store.clear()
    for k, turn in enumerate(turns):
        memories = pipeline.extract(turn, PRIYA)
        if pipeline.resolve is not None:
            memories = pipeline.resolve(memories, store.all())
        if raced and k and k % 4 == 0:
            snapshot = read(store)
            store.add(memories)
            write_back(store, snapshot, pipeline.consolidate(list(snapshot.memories)))
        else:
            store.add(memories)
    store.add(_agent_memories(PRIYA))
    run(store, pipeline.consolidate)
    return store


def test_the_raced_run_is_identical_to_the_serialised_one(env) -> None:
    """Non-destructive is not enough; it has to be correct."""
    pipeline, turns, root = env
    serial, raced = (
        _build(pipeline, turns, root, False),
        _build(pipeline, turns, root, True),
    )
    assert {m.id for m in serial.all()} == {m.id for m in raced.all()}
    assert len(raced.all()) == 37
    assert sum(m.is_live for m in raced.all()) == 30


def test_the_job_is_replayable(env) -> None:
    """A crashed job can simply be run again."""
    pipeline, turns, root = env
    store = _build(pipeline, turns, root, True)
    before = [(m.id, m.confidence, m.invalid_at) for m in store.all()]
    report = run(store, pipeline.consolidate)
    assert [(m.id, m.confidence, m.invalid_at) for m in store.all()] == before
    assert (report.kept, report.retired, report.untouched) == (37, 0, 0)


def test_a_deliberate_deletion_still_deletes(env) -> None:
    """Absence means two opposite things; the id set separates them."""
    pipeline, turns, root = env
    store = _grown_to(pipeline, turns, 10, root / "del.jsonl")
    snapshot = read(store)
    victim = snapshot.memories[0]
    computed = [m for m in snapshot.memories if m.id != victim.id]
    report = write_back(store, snapshot, computed)
    assert victim.id not in {m.id for m in store.all()}, "the job merged it away"
    assert report.retired == 1


def test_a_late_arrival_is_not_a_deletion(env) -> None:
    pipeline, turns, root = env
    store = _grown_to(pipeline, turns, 10, root / "late.jsonl")
    snapshot = read(store)
    late = pipeline.extract(turns[10], PRIYA)
    store.add(late)
    report = write_back(store, snapshot, list(snapshot.memories))
    assert report.untouched == len(late)
    assert all(m.id in {x.id for x in store.all()} for m in late)


def test_merge_keeps_what_the_job_created(env) -> None:
    """Summaries and merged records are new ids in neither store nor snapshot."""
    pipeline, turns, root = env
    store = _grown_to(pipeline, turns, 10, root / "new.jsonl")
    snapshot = read(store)
    invented = snapshot.memories[0]
    computed = [*snapshot.memories, invented.__class__(
        content="a summary the job wrote",
        type=invented.type,
        scope=invented.scope,
        provenance=invented.provenance,
        happened_at=invented.happened_at,
    )]
    merged = merge(store.all(), snapshot, computed)
    assert any(m.content == "a summary the job wrote" for m in merged)
