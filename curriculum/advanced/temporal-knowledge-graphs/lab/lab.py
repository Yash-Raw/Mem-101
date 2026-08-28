"""Lab: validity that travels through what was derived from it.

    uv run python curriculum/advanced/temporal-knowledge-graphs/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

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
    raise NotImplementedError("implement edges")


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
    raise NotImplementedError("implement orphans")


def cascade(memories: list[Memory], at: datetime) -> list[Memory]:
    """Retire, transitively, every live fact left with no live support.

    Runs to a fixed point: retiring a derived fact can orphan something
    derived from *it*. One pass is enough on this corpus and would not be on
    a store with summaries of summaries, which is the point of the loop.
    """
    raise NotImplementedError("implement cascade")


RETIRED_BY_ITS_OWN_DERIVED_FACT = "She works nights most of the month"


def _naive_orphans(memories):
    """Every source retired -- without asking who retired it."""
    by_id = {m.id: m for m in memories}
    out = []
    for m in memories:
        if not m.is_live or not m.derived_from:
            continue
        sources = [by_id[r] for r in m.derived_from if r in by_id]
        if sources and all(not s.is_live for s in sources):
            out.append(m)
    return out


def main() -> None:
    from dataclasses import replace as dc_replace

    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.graph import EntityGraph
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    store = JsonlStore("/tmp/memlab-cascade.jsonl")
    store.clear()
    ingest(store, Scope(user="priya"), at("A1"))
    memories = store.all()

    g = EntityGraph()
    g.build(memories)
    print("two graphs run through this store:\n")
    print(f"   entity graph      {g.shape()}")
    print(f"   derivation graph  {shape(memories)}")

    naive, correct = _naive_orphans(memories), orphans(memories)
    print("\n   orphans -- live facts whose sources are all retired:\n")
    print(f"   {'naive definition':34}{len(naive)}")
    print(f"   {'excluding self-supersession':34}{len(correct)}")
    for m in naive:
        source = next(
            s for s in memories if s.id in m.derived_from
        )
        print(f"\n   {m.content}   <- live, derived from")
        print(f"     {source.content}   <- retired, superseded_by this one")

    live_before = sum(m.is_live for m in memories)
    print(f"\n   cascade: live {live_before} -> "
          f"{sum(m.is_live for m in cascade(memories, datetime(2026, 8, 27, tzinfo=UTC)))}")

    derived = next(m for m in memories if m.derived_from)
    source = next(s for s in memories if s.id in derived.derived_from)
    broken = [
        dc_replace(m, derived_from=(source.provenance.source_id,))
        if m.id == derived.id
        else m
        for m in memories
    ]
    print("\n   the same zero, for the opposite reason:\n")
    print(f"   derived_from as a source_id  {shape(broken)}  orphans: "
          f"{len(orphans(broken))}")
    print(f"   derived_from as a memory id  {shape(memories)}  orphans: "
          f"{len(orphans(memories))}")


if __name__ == "__main__":
    main()
