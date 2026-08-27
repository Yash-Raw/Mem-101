"""Reference solution."""

from __future__ import annotations

from memlab.retrieve.embedding import Hit

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
