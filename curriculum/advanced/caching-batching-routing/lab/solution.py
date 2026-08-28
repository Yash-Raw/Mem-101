"""Reference solution."""

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
