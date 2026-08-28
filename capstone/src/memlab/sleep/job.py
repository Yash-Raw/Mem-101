"""Running consolidation as a job that something else is writing underneath.

`ingest()` consolidates with `store.replace(consolidate(store.all()))` -- a
read-modify-write with nothing between the read and the write. It is correct
exactly once: when the corpus has already finished arriving.

Give it a live conversation and a turn landing mid-job is destroyed by the
write-back. Summed over every position a one-turn job could occupy, that is
**33 memories**, and the worst single turn is session 8 -- the announcement of
the job change, all four memories, gone. The batch job that exists to keep the
store correct deletes the correction.

`sleep-time-compute` made this *more* likely, not less: it runs consolidation
eleven times instead of once.

The fix is not a lock. A job reads a snapshot and must write back only what it
was actually looking at:

    snapshot = read(store)          # remember WHICH ids were read
    computed = consolidate(snapshot.memories)
    write_back(store, snapshot, computed)

Anything the store gained since the read is not the job's to have an opinion
about, so it survives untouched.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..types import Memory


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
    memories = tuple(store.all())
    return Snapshot(memories=memories, ids=frozenset(m.id for m in memories))


def merge(current: list[Memory], snapshot: Snapshot, computed: list[Memory]) -> list[Memory]:
    """The job's result for what it read; the store's own for everything else.

    Order follows `current` so the log stays append-ordered, with anything the
    job newly created appended. Consolidation legitimately removes memories --
    a merged duplicate is gone on purpose -- so an id in the snapshot and not
    in `computed` is dropped. An id in neither is *kept*: it arrived late.
    """
    by_id = {m.id: m for m in computed}
    out: list[Memory] = []
    for memory in current:
        if memory.id not in snapshot.ids:
            out.append(memory)          # arrived after the read
        elif memory.id in by_id:
            out.append(by_id[memory.id])  # the job's version
        # else: the job merged it away, on purpose
    seen = {m.id for m in out}
    out.extend(m for m in computed if m.id not in seen)  # summaries, merges
    return out


def write_back(store, snapshot: Snapshot, computed: list[Memory]) -> WriteBack:
    """Merge the job's output into the store as it stands now."""
    current = store.all()
    merged = merge(current, snapshot, computed)
    by_id = {m.id: m for m in computed}
    report = WriteBack(
        kept=sum(1 for m in current if m.id in snapshot.ids and m.id in by_id),
        retired=sum(1 for m in current if m.id in snapshot.ids and m.id not in by_id),
        untouched=sum(1 for m in current if m.id not in snapshot.ids),
        total=len(merged),
    )
    store.replace(merged)
    return report


def run(store, consolidate) -> WriteBack:
    """Read, compute, merge. The three lines every background job needs."""
    snapshot = read(store)
    return write_back(store, snapshot, consolidate(list(snapshot.memories)))
