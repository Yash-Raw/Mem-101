"""Lab: the cap is a correctness parameter.

    uv run python curriculum/intermediate/budgeted-forgetting/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.types import Memory, Tier

DEFAULT_CAP = 20


@dataclass
class Eviction:
    memory: Memory
    from_tier: Tier
    to_tier: Tier
    reason: str


def enforce(
    memories: list[Memory], cap: int = DEFAULT_CAP
) -> tuple[list[Memory], list[Eviction]]:
    """TODO: keep the `cap` most salient live LONG_TERM memories; demote the rest.

    Demote to Tier.WORKING -- one step, so reinforcement can lift a memory back.
    Return (all memories with tiers updated, the evictions). Nothing is removed:
    len(out) must equal len(memories).
    """
    raise NotImplementedError("implement enforce")


def retrievable(memories: list[Memory]) -> list[Memory]:
    """What default retrieval sees: live, and not demoted out of the way."""
    return [m for m in memories if m.is_live and m.tier is Tier.LONG_TERM]


def cap_sweep(memories: list[Memory], caps=(20, 16, 12, 8)) -> list[tuple]:
    """(cap, retrievable, store size, exam correct, first casualty)."""
    from memlab.eval.exam import exam_answer
    from memlab.types import Scope

    scope = Scope(user="priya")
    baseline = {m.id for m in retrievable(memories)}
    rows = []
    for cap in caps:
        capped, evictions = enforce(memories, cap=cap)
        kept = retrievable(capped)
        answer = exam_answer(kept, scope)
        lost = [e.memory.content for e in evictions if e.memory.id in baseline]
        rows.append((cap, len(kept), len(capped), answer.is_correct,
                     sorted(answer.avoid), lost))
    return rows


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    store = JsonlStore("/tmp/memlab-budget.jsonl")
    store.clear()
    ingest(store, Scope(user="priya"), at("I5"))
    memories = store.all()

    print(f"retrievable at I5: {len(retrievable(memories))}  (cap is {DEFAULT_CAP})")
    print("the cap does not bind yet -- the mechanism exists ahead of the pressure\n")
    print(f"  {'cap':>4}{'retrievable':>13}{'store':>7}  exam")
    for cap, kept, size, ok, avoid, lost in cap_sweep(memories):
        verdict = "CORRECT" if ok else f"broken -- avoid={avoid}"
        print(f"  {cap:>4}{kept:>13}{size:>7}  {verdict}")
        for content in lost[:2]:
            print(f"       evicted: {content[:54]}")

    print("\nStore size never changes. Eviction is demotion, not deletion.")


if __name__ == "__main__":
    main()
