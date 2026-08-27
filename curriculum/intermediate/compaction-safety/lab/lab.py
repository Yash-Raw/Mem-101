"""Lab: a policy derived from the question, not a list of topics.

    uv run python curriculum/intermediate/compaction-safety/lab/lab.py
"""

from __future__ import annotations

from memlab.evolve.conflict import slot_of
from memlab.retrieve.embedding import Hit
from memlab.retrieve.query import slots_for


def required(hits: list[Hit], per_slot: int = 3) -> list[Hit]:
    """TODO: hits covering the slots their own sub-questions asked about.

    Use slots_for(hit.query) for what was asked and slot_of(hit.memory) for
    what a memory fills. Breadth first across slots, then depth up to
    per_slot -- so a question with three relevant facts is not starved by a
    question with one.
    """
    raise NotImplementedError("implement required")


def unpinned(hits: list[Hit], pinned: list[Hit]) -> list[Hit]:
    ids = {h.memory.id for h in pinned}
    return [h for h in hits if h.memory.id not in ids]


def main() -> None:
    from memlab.app.chat import ask, ingest
    from memlab.assemble.budget import pack
    from memlab.eval.exam import QUESTION
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    NEEDED = ("works at Calico", "does not eat meat", "eats fish", "gluten")
    scope = Scope(user="priya")
    pipeline = at("I7")
    store = JsonlStore("/tmp/memlab-pinning.jsonl")
    store.clear()
    ingest(store, scope, pipeline)
    pipeline.vectors.index(store.all())
    _ctx, hits = ask(store, scope, QUESTION, k=5, pipeline=pipeline)

    asked = {q: slots_for(q) for q in {h.query for h in hits}}
    print("slots the question asked about:")
    for query, slots in asked.items():
        print(f"   {query!r} -> {slots}")

    print("\npinned, breadth first across slots:")
    for hit in required(hits):
        print(f"   [{slot_of(hit.memory):<9}] {hit.memory.content[:46]}")

    def complete(budget, pin):
        out = pack(hits, budget_tokens=budget, pin=pin)
        return "PASS" if all(any(n in h.memory.content for h in out.kept)
                             for n in NEEDED) else "fail"

    print(f"\n{'budget':>7}{'score order':>13}{'pinned':>9}")
    for b in (80, 77, 70, 67):
        print(f"{b:>7}{complete(b, False):>13}{complete(b, True):>9}")

    print("\nIdentical. Breadth-first reaches the employer slot's second fact")
    print("before the diet slot's third. The invariant it buys is coverage:")
    covered = {slot_of(h.memory) for h in required(hits)}
    print(f"   every asked slot covered: {covered >= set().union(*asked.values())}")


if __name__ == "__main__":
    main()
