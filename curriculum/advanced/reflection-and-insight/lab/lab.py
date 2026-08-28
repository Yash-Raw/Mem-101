"""Lab: derive higher-order beliefs, and refuse to derive most of them.

    uv run python curriculum/advanced/reflection-and-insight/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from memlab.types import Memory, Scope


class Refusal(Enum):
    """Why a group was not turned into a belief."""

    THIRD_PARTY = "third party"      # the facts are about someone else
    TOO_FEW = "too few"              # one belief is not a synthesis


@dataclass(frozen=True)
class Group:
    slot: str
    members: tuple[Memory, ...]
    refusal: Refusal | None = None

    @property
    def ok(self) -> bool:
        return self.refusal is None


def groups(memories: list[Memory], scope: Scope) -> list[Group]:
    """Live beliefs sharing a slot, with the reason each is or is not usable."""
    raise NotImplementedError("implement groups")


def _refuse(live: tuple[Memory, ...]) -> Refusal | None:
    """Why not to compose. Retired members are not a reason -- they are simply
    not members: the composite is built from what is live, so the history the
    slot carries is untouched and `temporal-questions` still answers it.
    """
    raise NotImplementedError("implement _refuse")


def compose(group: Group, scope: Scope) -> Memory:
    """One belief from several, traceable to every source.

    Template, not generation. A composed insight can be checked against its
    members; a written one is a sentence with no way back to the evidence,
    and this is the stage where an unsupported claim would enter the store
    looking exactly like a supported one.
    """
    raise NotImplementedError("implement compose")


def reflect(memories: list[Memory], scope: Scope) -> list[Memory]:
    """The derived beliefs, and nothing else."""
    return [compose(g, scope) for g in groups(memories, scope) if g.ok]


SC = None  # set in main


def _lowest_passing(memories, pipeline, scope):
    from memlab.eval.exam import exam_from_context

    for budget in range(40, 90):
        if exam_from_context(
            memories, scope, k=5, pipeline=pipeline, budget=budget
        ).is_correct:
            return budget
    return None


def main() -> None:
    from dataclasses import replace as dc_replace
    from datetime import UTC, datetime

    from memlab.app.chat import ask, ingest
    from memlab.eval.exam import QUESTION
    from memlab.evolve.promote import analyse
    from memlab.pipeline import at
    from memlab.retrieve.scoped import eligible
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    now = datetime(2026, 8, 27, tzinfo=UTC)

    def fresh():
        pipeline = at("A2")
        store = JsonlStore(f"/tmp/memlab-reflect-{id(pipeline)}.jsonl")
        store.clear()
        ingest(store, scope, pipeline)
        return store, pipeline

    store, pipeline = fresh()
    report = analyse(store.all(), scope)
    print(f"similarity generator: {len(report.candidates)} candidates, "
          f"{len(report.promoted)} promoted\n")
    for c in report.candidates[:4]:
        print(f"   {c.similarity:.3f}  {c.a.content[:31]:33} + {c.b.content[:34]}")

    print("\n   generating from structure instead:\n")
    for g in groups(store.all(), scope):
        verdict = "DERIVE" if g.ok else f"refuse: {g.refusal.value}"
        print(f"   {g.slot:18} live={len(g.members)}  {verdict}")

    insights = reflect(store.all(), scope)
    print(f"\n   derived {len(insights)}:\n")
    for m in insights:
        print(f"   {m.content[:92]}")

    store.add(insights)
    pool = eligible(store.all(), scope)
    print(f"\n   eligible pool: {len(pool)} of {len(store.all())}")
    print(f"   insights in the pool: "
          f"{sum(1 for m in pool if m.id in {x.id for x in insights})} of {len(insights)}")

    store.replace(pipeline.decay(store.all()))
    pipeline.vectors.index(store.all())
    print("\n   scored, and retrieved:\n")
    for i, hit in enumerate(ask(store, scope, QUESTION, k=5, pipeline=pipeline)[1], 1):
        tag = "  <- derived" if hit.memory.id in {m.id for m in insights} else ""
        print(f"   {i}. {hit.score:.3f} {hit.memory.content[:56]}{tag}")

    print(f"\n   {'policy':36}{'lowest passing budget':>22}{'store':>7}")
    base, base_pipeline = fresh()
    rows = [("no reflection", base.all(), base_pipeline)]

    joined, joined_pipeline = fresh()
    joined.add(reflect(joined.all(), scope))
    joined.replace(joined_pipeline.decay(joined.all()))
    rows.append(("insights added alongside", joined.all(), joined_pipeline))

    swapped, swapped_pipeline = fresh()
    derived = reflect(swapped.all(), scope)
    sources = {i for m in derived for i in m.derived_from}
    swapped.replace([
        dc_replace(m, invalid_at=now,
                   superseded_by=next(x.id for x in derived if m.id in x.derived_from))
        if m.id in sources else m
        for m in swapped.all()
    ] + derived)
    swapped.replace(swapped_pipeline.decay(swapped.all()))
    rows.append(("insights retire their sources", swapped.all(), swapped_pipeline))

    for label, memories, pipe in rows:
        print(f"   {label:36}{_lowest_passing(memories, pipe, scope):>22}"
              f"{len(memories):>7}")


if __name__ == "__main__":
    main()
