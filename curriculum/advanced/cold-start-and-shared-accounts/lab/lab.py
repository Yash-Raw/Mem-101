"""Lab: how a model fills up, and what a shared account does to it.

    uv run python curriculum/advanced/cold-start-and-shared-accounts/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.types import Memory, Scope
from memlab.user.apply import apply
from memlab.user.model import UserModel, build


@dataclass(frozen=True)
class Coverage:
    """The model at one point in a conversation."""

    turn: int
    memories: int
    attributes: tuple[str, ...]

    @property
    def size(self) -> int:
        return len(self.attributes)


def growth(
    snapshots: list[tuple[int, list[Memory]]], scope: Scope
) -> list[Coverage]:
    """Model size after each of a sequence of stores."""
    raise NotImplementedError("implement growth")


def answerable(model: UserModel, question: str, scope: Scope, needed) -> bool:
    """Whether the attributes this question reaches actually contain the facts.

    Distinct from "is the model complete". Coverage counts attributes; this
    reads their contents, and the two milestones are two turns apart on this
    corpus -- in the direction that makes a coverage check optimistic.
    """
    raise NotImplementedError("implement answerable")


def merged(memories: list[Memory], scope: Scope) -> UserModel:
    """The model a shared account produces: entity links discarded.

    Not a hypothetical. Two people already appear in this store, and the only
    thing keeping the second out of the first's model is the `entities` field
    I2 populates.
    """
    raise NotImplementedError("implement merged")


QUESTION = "where do I work and what should I not eat?"
NEEDED = ("Calico", "does not eat meat", "eats fish", "gluten")
MILESTONES = (1, 3, 8, 12, 20, 24)


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.fixtures import load_turns
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    pipeline = at("A3")
    turns = [t for t in load_turns(user_only=True) if t["session"] < 14]

    store = JsonlStore("/tmp/memlab-coverage.jsonl")
    store.clear()
    snapshots, first_reached, complete, first_answer = [], None, None, None
    for i, turn in enumerate(turns, 1):
        memories = pipeline.extract(turn, scope)
        if pipeline.resolve is not None:
            memories = pipeline.resolve(memories, store.all())
        store.add(memories)
        store.replace(pipeline.consolidate(store.all()))
        model = build(store.all(), scope)
        if i in MILESTONES:
            snapshots.append((i, store.all()))
        if first_reached is None and apply(model, QUESTION, scope).asked:
            first_reached = i
        if complete is None and len(model.attributes) == 6:
            complete = i
        if first_answer is None and answerable(model, QUESTION, scope, NEEDED):
            first_answer = i

    for coverage in growth(snapshots, scope):
        print(f"   turn {coverage.turn:>2}  {coverage.memories:>2} memories  "
              f"{coverage.size} attributes  {list(coverage.attributes)}")

    print(f"\n   first attribute the question reaches   turn {first_reached}")
    print(f"   model complete (6 of 6 attributes)     turn {complete}")
    print(f"   first turn it answers the exam fully   turn {first_answer}")

    whole = JsonlStore("/tmp/memlab-coverage-full.jsonl")
    whole.clear()
    ingest(whole, scope, pipeline)
    intact = build(whole.all(), scope)
    shared = merged(whole.all(), scope)
    print(f"\n   entities intact     {len(intact.attributes)} attributes")
    print(f"   entities stripped   {len(shared.attributes)} attributes")
    for slot in sorted(set(shared.attributes) - set(intact.attributes)):
        for belief in shared.attributes[slot].beliefs:
            print(f"      [{slot}] {belief.content}")


if __name__ == "__main__":
    main()
