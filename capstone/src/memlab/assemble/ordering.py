"""How a memory is rendered, and what the rendering costs.

Every element in the context is paid for in tokens, including the ones that are
not memories. The line format is one of them.

    - [2025-12-08] Priya works at Calico Systems     dated, 11 tokens
    - [2025] Priya works at Calico Systems           year,  10
    - Priya works at Calico Systems                  bare,   9

Across the four facts the exam needs that is 38, 32 or 25 tokens -- a 34%
difference from a formatting choice.

The dates are not decoration. `context-assembly-v0` added them because a model
cannot resolve two contradictory memories without knowing which is older, and
until supersession existed that was the only signal available. Now that I4
retires the loser, full precision buys less than it did -- but not nothing, and
`relevance-vs-truth` is why: a live fact can still be old.

Year precision keeps the recency ordering and returns six tokens. That is the
trade, and it is only visible once someone measures it.
"""
from __future__ import annotations

from ..retrieve.embedding import Hit

DATED = "dated"
YEAR = "year"
BARE = "bare"


def render(hit: Hit, precision: str = DATED) -> str:
    """One memory, one line. Never truncated -- half a fact is a hazard."""
    when = hit.memory.happened_at
    if precision == BARE or when is None:
        return f"- {hit.memory.content}"
    stamp = when.date().isoformat() if precision == DATED else str(when.year)
    return f"- [{stamp}] {hit.memory.content}"


def order(hits: list[Hit]) -> list[Hit]:
    """Score order, not chronological.

    Attention degrades over long spans, so the most relevant memory belongs
    first. Chronological ordering reads more naturally and buries the best
    answer in the middle, which is the one place it is least likely to be used.
    """
    return sorted(hits, key=lambda h: -h.score)
