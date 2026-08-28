"""Lab: decide which turns cannot wait for the batch.

    uv run python curriculum/advanced/sleep-time-compute/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from memlab.types import Memory, MemoryType


class Gate(Enum):
    NEVER = "never"        # defer everything to the batch
    ALWAYS = "always"      # consolidate on every turn
    TYPE = "type"          # ...when a standing belief was written
    CONTESTED = "contested"  # ...when the turn claims an occupied slot


@dataclass(frozen=True)
class Schedule:
    """What has to happen before the next turn is answered."""

    gate: Gate = Gate.CONTESTED
    inline_types: frozenset[MemoryType] = frozenset({MemoryType.SEMANTIC})

    @classmethod
    def default(cls) -> Schedule:
        return cls(gate=Gate.CONTESTED)

    @classmethod
    def never(cls) -> Schedule:
        return cls(gate=Gate.NEVER)

    @classmethod
    def always(cls) -> Schedule:
        return cls(gate=Gate.ALWAYS)

    @classmethod
    def by_type(cls) -> Schedule:
        return cls(gate=Gate.TYPE)

    def needs_inline(self, written: list[Memory], stored: list[Memory]) -> bool:
        """Does this turn's output have to be consolidated before we answer?

        `stored` is the store as it stood *before* this turn -- the slots
        already claimed. Passing the post-write store makes every turn
        contested by its own writes.
        """
        raise NotImplementedError("implement needs_inline")


STALE = "data engineer at Northwind"


def _stale(store) -> int:
    return sum(1 for m in store.all() if m.is_live and STALE in m.content)


def main() -> None:
    import memlab.evolve.dedupe as dedupe_mod
    from memlab.app.chat import _agent_memories
    from memlab.fixtures import load_turns
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    pipeline = at("A2")
    turns = [t for t in load_turns(user_only=True) if t["session"] < 14]

    # The reference: consolidated after every turn, uninstrumented.
    reference, eager = [], JsonlStore("/tmp/memlab-sleep-ref.jsonl")
    eager.clear()
    for turn in turns:
        memories = pipeline.extract(turn, scope)
        if pipeline.resolve is not None:
            memories = pipeline.resolve(memories, eager.all())
        eager.add(memories)
        eager.replace(pipeline.consolidate(eager.all()))
        reference.append(_stale(eager))

    def walk(schedule):
        counts = {"embed": 0, "cosine": 0}
        embed, cosine = dedupe_mod.embed_text, dedupe_mod.cosine
        dedupe_mod.embed_text = lambda *a, **k: (
            counts.__setitem__("embed", counts["embed"] + 1), embed(*a, **k)
        )[1]
        dedupe_mod.cosine = lambda *a, **k: (
            counts.__setitem__("cosine", counts["cosine"] + 1), cosine(*a, **k)
        )[1]

        store = JsonlStore("/tmp/memlab-sleep-walk.jsonl")
        store.clear()
        runs, wrong = 0, 0
        for i, turn in enumerate(turns):
            before = store.all()
            memories = pipeline.extract(turn, scope)
            if pipeline.resolve is not None:
                memories = pipeline.resolve(memories, before)
            store.add(memories)
            if schedule.needs_inline(memories, before):
                store.replace(pipeline.consolidate(store.all()))
                runs += 1
            if _stale(store) != reference[i]:
                wrong += 1
        store.add(_agent_memories(scope))
        store.replace(pipeline.consolidate(store.all()))
        runs += 1

        dedupe_mod.embed_text, dedupe_mod.cosine = embed, cosine
        return runs, counts["embed"], counts["cosine"], wrong, sum(
            m.is_live for m in store.all()
        )

    print("what decides whether a turn can wait:\n")
    print(f"   {'gate':32}{'runs':>6}{'embed':>8}{'cosine':>9}{'wrong':>7}{'live':>6}")
    for label, schedule in (
        ("never -- defer everything", Schedule.never()),
        ("by memory type", Schedule.by_type()),
        ("by contested slot (default)", Schedule.default()),
        ("always -- every turn", Schedule.always()),
    ):
        runs, embed, cosine, wrong, live = walk(schedule)
        print(f"   {label:32}{runs:>6}{embed:>8}{cosine:>9}{wrong:>7}{live:>6}")


if __name__ == "__main__":
    main()
