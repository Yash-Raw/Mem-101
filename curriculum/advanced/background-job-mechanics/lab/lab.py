"""Lab: run consolidation as a job something else is writing underneath.

    uv run python curriculum/advanced/background-job-mechanics/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.types import Memory


@dataclass(frozen=True)
class Snapshot:
    """What a job read, and the ids it is therefore entitled to rewrite."""

    memories: tuple[Memory, ...]
    ids: frozenset[str]

    @property
    def size(self) -> int:
        return len(self.memories)


@dataclass(frozen=True)
class WriteBack:
    """What the merge did, so a job that quietly loses data cannot stay quiet."""

    kept: int        # rewritten by the job
    retired: int     # the job merged them away
    untouched: int   # arrived after the read; not the job's business
    total: int


def read(store) -> Snapshot:
    """Take a snapshot, recording which ids it covers.

    The id set is the whole mechanism. Without it the write-back cannot tell
    "the job deleted this" from "the job never saw it", and the two are
    indistinguishable in the output -- both are simply absent.
    """
    raise NotImplementedError("implement read")


def merge(current: list[Memory], snapshot: Snapshot, computed: list[Memory]) -> list[Memory]:
    """The job's result for what it read; the store's own for everything else.

    Order follows `current` so the log stays append-ordered, with anything the
    job newly created appended. Consolidation legitimately removes memories --
    a merged duplicate is gone on purpose -- so an id in the snapshot and not
    in `computed` is dropped. An id in neither is *kept*: it arrived late.
    """
    raise NotImplementedError("implement merge")


def write_back(store, snapshot: Snapshot, computed: list[Memory]) -> WriteBack:
    """Merge the job's output into the store as it stands now."""
    raise NotImplementedError("implement write_back")


def run(store, consolidate) -> WriteBack:
    """Read, compute, merge. The three lines every background job needs."""
    snapshot = read(store)
    return write_back(store, snapshot, consolidate(list(snapshot.memories)))


SESSION_8 = 13  # index of the turn that announces the job change


def _pipeline_and_turns():
    from memlab.fixtures import load_turns
    from memlab.pipeline import at

    return at("A2"), [t for t in load_turns(user_only=True) if t["session"] < 14]


def _grown_to(pipeline, turns, k, path):
    """A store as it stands after k turns, consolidated."""
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    store = JsonlStore(path)
    store.clear()
    for turn in turns[:k]:
        memories = pipeline.extract(turn, Scope(user="priya"))
        if pipeline.resolve is not None:
            memories = pipeline.resolve(memories, store.all())
        store.add(memories)
    store.replace(pipeline.consolidate(store.all()))
    return store


def _race(pipeline, turns, k, guarded):
    """Start a job, land turn k while it computes, then write back."""
    from memlab.types import Scope

    store = _grown_to(pipeline, turns, k, "/tmp/memlab-job-race.jsonl")
    snapshot = read(store)
    late = pipeline.extract(turns[k], Scope(user="priya"))
    if pipeline.resolve is not None:
        late = pipeline.resolve(late, store.all())
    store.add(late)
    computed = pipeline.consolidate(list(snapshot.memories))
    if guarded:
        write_back(store, snapshot, computed)
    else:
        store.replace(computed)
    surviving = {m.id for m in store.all()}
    return store, [m for m in late if m.id not in surviving], snapshot


def main() -> None:
    from memlab.app.chat import _agent_memories
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    pipeline, turns = _pipeline_and_turns()

    store = _grown_to(pipeline, turns, 20, "/tmp/memlab-job-demo.jsonl")
    snapshot = read(store)
    print(f"store before the job          {snapshot.size}")
    late = pipeline.extract(turns[20], Scope(user="priya"))
    if pipeline.resolve is not None:
        late = pipeline.resolve(late, store.all())
    store.add(late)
    print(f"a turn lands mid-job          {len(store.all())}")
    store.replace(pipeline.consolidate(list(snapshot.memories)))
    print(f"after the job writes back     {len(store.all())}")

    print("\n   memories destroyed, summed over every one-turn position:\n")
    for label, guarded in (("replace (as shipped)", False),
                           ("merge against the snapshot", True)):
        total = sum(len(_race(pipeline, turns, k, guarded)[1])
                    for k in range(1, len(turns)))
        print(f"   {label:32}{total:>5}")

    _s, lost, _snap = _race(pipeline, turns, SESSION_8, False)
    print(f"\n   the worst single turn -- session 8, {len(lost)} memories:\n")
    for m in lost:
        print(f"     {m.content}")

    def build(raced):
        st = JsonlStore(f"/tmp/memlab-job-{raced}.jsonl")
        st.clear()
        for k, turn in enumerate(turns):
            memories = pipeline.extract(turn, Scope(user="priya"))
            if pipeline.resolve is not None:
                memories = pipeline.resolve(memories, st.all())
            if raced and k and k % 4 == 0:
                snap = read(st)
                st.add(memories)
                write_back(st, snap, pipeline.consolidate(list(snap.memories)))
            else:
                st.add(memories)
        st.add(_agent_memories(Scope(user="priya")))
        run(st, pipeline.consolidate)
        return st

    serial, raced = build(False), build(True)
    print(f"\n   serialised     {len(serial.all())} memories, "
          f"{sum(m.is_live for m in serial.all())} live")
    print(f"   raced+guarded  {len(raced.all())} memories, "
          f"{sum(m.is_live for m in raced.all())} live")
    print(f"   identical ids: "
          f"{ {m.id for m in serial.all()} == {m.id for m in raced.all()} }")

    before = [(m.id, m.confidence, m.invalid_at) for m in raced.all()]
    report = run(raced, pipeline.consolidate)
    after = [(m.id, m.confidence, m.invalid_at) for m in raced.all()]
    print(f"\n   re-running the job is a no-op: {before == after}")
    print(f"   {report}")


if __name__ == "__main__":
    main()
