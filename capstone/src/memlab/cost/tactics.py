"""Three cost tactics, and which of them this system can actually use.

    caching   reuse a result keyed on something stable
    batching  send many items in one call
    routing   send cheap work to a cheap model

`cost-model` measured 48 model calls and 38 embeddings on the write path, and
0 calls on the read. Applied against that profile:

**Caching is already done and it is the embeddings, not the calls.** `VectorIndex`
is keyed on the content-addressed id, which is why a warm read costs 2 embeds
and a cold one costs 20. Caching *completions* is the tactic everyone reaches
for and it buys nothing here -- every turn's text is different, so the cache
key never repeats.

**Batching is available and changes the count, not the work.** Extraction is
one call per turn because turns arrive one at a time; a backfill can batch.
The measurement worth having is how many calls a batched ingest makes, and
whether the fake's fixture keying survives it -- which it does not, and that
is the finding.

**Routing is the one with headroom, and there are two targets rather than
one.** `latency-budget` measured the per-turn cost as an even split:
extraction, synchronous, and `conflict.classify`, entirely deferred. Both are
bounded tasks -- a schema and four labels -- which is the shape small models
fit. *Arbitration* is the stage with nothing to route, because
`deterministic-freshness` made it rules; conflict **detection** is a model
call, and an earlier version of this file confused the two.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tactic:
    name: str
    applies: bool
    saving: str
    why: str


def assess(write_calls: int, write_embeds: int, read_calls: int) -> list[Tactic]:
    """What each tactic is worth against a measured profile."""
    return [
        Tactic(
            "cache completions",
            False,
            "nothing",
            "every turn's text differs, so the key never repeats",
        ),
        Tactic(
            "cache embeddings",
            True,
            "18 embeds per read",
            "content-addressed ids; already shipped as VectorIndex",
        ),
        Tactic(
            "batch extraction",
            True,
            f"{write_calls} calls -> fewer, same work",
            "only on backfill; live turns arrive one at a time",
        ),
        Tactic(
            "route extraction to a small model",
            True,
            "50% of the per-turn cost",
            "bounded, schema-constrained output -- the shape small models fit",
        ),
        Tactic(
            "route conflict detection",
            True,
            "the other 50%",
            "four labels out -- A7.5's one judgement site, bounded by design",
        ),
        Tactic(
            "route arbitration",
            False,
            "nothing",
            "already rules; there is no model call to route",
        ),
    ]


def headroom(tactics: list[Tactic]) -> tuple[int, int]:
    """(tactics that apply, total considered)."""
    return sum(1 for t in tactics if t.applies), len(tactics)


def already_shipped(tactics: list[Tactic]) -> list[str]:
    """The ones this course built before it had a cost lesson."""
    return [t.name for t in tactics if t.applies and "already" in t.why]
