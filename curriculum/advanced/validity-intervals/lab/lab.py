"""Lab: ask what was true then, and what we believed then.

    uv run python curriculum/advanced/validity-intervals/lab/lab.py
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from memlab.temporal.clocks import event_end, event_start
from memlab.types import Memory


def held_at(m: Memory, when: datetime) -> bool:
    """Was this fact true at `when`, on the event axis?

    An open interval -- `valid_to` unset -- means "still true as far as anyone
    said". That is the honest reading: nothing in the corpus says the cycling
    stopped, only that a later memory describes a train.
    """
    raise NotImplementedError("implement held_at")


def believed_at(m: Memory, when: datetime) -> bool:
    """Did the store hold this belief at `when`, on the belief axis?"""
    raise NotImplementedError("implement believed_at")


def as_of(
    memories: list[Memory],
    when: datetime,
    believed_at_time: datetime | None = None,
) -> list[Memory]:
    """Facts true at `when`, optionally as the store saw things at another time.

    Omit `believed_at_time` and you get the store's *current* account of the
    past -- corrections included. Pass it and you get the account it would
    have given then, mistakes and all. Both are legitimate; conflating them is
    how an audit trail stops being one.
    """
    raise NotImplementedError("implement as_of")


def changed_between(
    memories: list[Memory], start: datetime, end: datetime
) -> list[tuple[Memory, str]]:
    """What moved on either axis in the window, and which axis moved.

    Returns (memory, axis) with axis in {"became true", "stopped being true",
    "believed", "retired"}. Four kinds of change, because there are two axes
    and each has two ends -- and a changelog that reports only "retired" tells
    you when the system noticed, never when the world moved.
    """
    events: list[tuple[Memory, str]] = []
    for m in memories:
        vs, ve = event_start(m), event_end(m)
        if vs and start <= vs < end:
            events.append((m, "became true"))
        if ve and start <= ve < end:
            events.append((m, "stopped being true"))
        if start <= m.recorded_at < end:
            events.append((m, "believed"))
        if m.invalid_at and start <= m.invalid_at < end:
            events.append((m, "retired"))
    return sorted(events, key=lambda e: _stamp(e[0], e[1]))


def _stamp(m: Memory, axis: str) -> datetime:
    return {
        "became true": event_start(m),
        "stopped being true": event_end(m),
        "believed": m.recorded_at,
        "retired": m.invalid_at,
    }[axis]


EMPLOYER = ("Northwind", "Calico")
JUNE_2025 = datetime(2025, 6, 1, tzinfo=UTC)
NOW = datetime(2026, 8, 27, tzinfo=UTC)
SWEEP_FROM, SWEEP_TO = datetime(2025, 3, 1, tzinfo=UTC), datetime(2026, 9, 1, tzinfo=UTC)


def _build(pipeline):
    from memlab.app.chat import ingest
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    store = JsonlStore(f"/tmp/memlab-validity-{pipeline.name}.jsonl")
    store.clear()
    ingest(store, Scope(user="priya"), pipeline)
    return store.all()


def _employer(memories):
    return [m for m in memories if any(e in m.content for e in EMPLOYER)]


def _sweep(memories):
    """Days on which the two questions give different answers."""
    differ, total, day = 0, 0, SWEEP_FROM
    while day < SWEEP_TO:
        total += 1
        if {m.id for m in as_of(memories, day)} != {
            m.id for m in as_of(memories, day, believed_at_time=day)
        }:
            differ += 1
        day += timedelta(days=1)
    return differ, total


def main() -> None:
    from dataclasses import replace as dc_replace

    from memlab.pipeline import _resolve_dedupe_reconcile_bitemporal, at

    # A1 before its parser lands -- see the lesson's "Design decisions".
    before_the_parser = at("A1").with_stage(
        anchor=None, consolidate=_resolve_dedupe_reconcile_bitemporal
    )
    i8, a1 = _build(at("I8")), _build(before_the_parser)

    print("\"what did you believe about my employer in June 2025?\"\n")
    for m in _employer(as_of(a1, JUNE_2025)):
        print(f"   {m.content}")
    print("\n   (the Level 2 read path answers with four facts about Calico,")
    print("    a job she had not been offered yet)\n")

    print(f"   {'':44}{'@I8':>6}{'@A1':>6}")
    rows = [
        ("facts with a recorded end",
         sum(1 for m in i8 if m.valid_to), sum(1 for m in a1 if m.valid_to)),
        ("beliefs retired before they were recorded",
         sum(1 for m in i8 if m.invalid_at and m.invalid_at < m.recorded_at),
         sum(1 for m in a1 if m.invalid_at and m.invalid_at < m.recorded_at)),
        ("\"what is true now?\" -> employer facts",
         len(_employer(as_of(i8, NOW))), len(_employer(as_of(a1, NOW)))),
    ]
    for label, a, b in rows:
        print(f"   {label:44}{a:>6}{b:>6}")

    print(f"\n   distinct recorded_at dates: {len({m.recorded_at.date() for m in a1})}"
          " (it was 1 when the belief clock was now())")

    differ, total = _sweep(a1)
    print(f"\n   dates where \"true then\" and \"believed then\" differ: "
          f"{differ} of {total}")

    anchored = [
        dc_replace(m, valid_from=datetime(2025, 8, 2, tzinfo=UTC))
        if "before the move" in m.content
        else m
        for m in a1
    ]
    differ2, _ = _sweep(anchored)
    print(f"   after anchoring one phrase:                            "
          f"{differ2} of {total}")


if __name__ == "__main__":
    main()
