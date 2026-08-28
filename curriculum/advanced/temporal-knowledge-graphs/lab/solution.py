"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from memlab.types import Memory


@dataclass(frozen=True)
class Edge:
    """`derived` was built from `source`."""

    derived: str
    source: str
    resolved: bool  # False when the reference matches nothing in the store


def edges(memories: list[Memory]) -> list[Edge]:
    """Every derivation edge, including the ones that point nowhere.

    Resolution is by memory id. A reference that does not match one is
    reported rather than dropped -- an unresolvable edge is exactly the case
    a cascade fails on, and a function that quietly returns fewer edges is
    how that failure stays invisible.
    """
    by_id = {m.id for m in memories}
    return [
        Edge(derived=m.id, source=ref, resolved=ref in by_id)
        for m in memories
        for ref in m.derived_from
    ]


def shape(memories: list[Memory]) -> dict[str, int]:
    e = edges(memories)
    return {
        "derived": sum(1 for m in memories if m.derived_from),
        "edges": len(e),
        "unresolvable": sum(1 for x in e if not x.resolved),
    }


def orphans(memories: list[Memory]) -> list[Memory]:
    """Live facts whose every supporting memory has been retired *by someone else*.

    The qualifier is the whole function. Consolidation retires the loser of a
    merge and hands its evidence to the winner, so a healthy derived fact is
    *always* built on a retired source -- the one it superseded. Counting that
    as an orphan retires a correct belief, and it is the first thing a naive
    cascade does on this corpus.

    An orphan is not automatically wrong either; a conclusion can outlive its
    evidence. But it is never *nothing*, and a store that cannot list these
    cannot tell a belief that was re-derived from one left standing because
    nobody looked.
    """
    by_id = {m.id: m for m in memories}
    out = []
    for m in memories:
        if not m.is_live or not m.derived_from:
            continue
        sources = [by_id[r] for r in m.derived_from if r in by_id]
        if not sources:
            continue
        stranded = [s for s in sources if not s.is_live and s.superseded_by != m.id]
        if len(stranded) == len(sources):
            out.append(m)
    return out


def cascade(memories: list[Memory], at: datetime) -> list[Memory]:
    """Retire, transitively, every live fact left with no live support.

    Runs to a fixed point: retiring a derived fact can orphan something
    derived from *it*. One pass is enough on this corpus and would not be on
    a store with summaries of summaries, which is the point of the loop.
    """
    out = list(memories)
    while True:
        stranded = orphans(out)
        if not stranded:
            return out
        ids = {m.id for m in stranded}
        out = [
            replace(m, invalid_at=at, valid_to=m.valid_to or at) if m.id in ids else m
            for m in out
        ]
