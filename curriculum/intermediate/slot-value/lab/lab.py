"""Lab: price every element, including the ones that are not memories.

    uv run python curriculum/intermediate/slot-value/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.assemble.ordering import render
from memlab.assemble.simple import HEADER, estimate_tokens
from memlab.retrieve.embedding import Hit

# Same job, 18 fewer tokens. "Recalled" carries the belief framing; "may be out
# of date" carries the staleness warning. The full version says both twice.
COMPACT_HEADER = "Recalled about this user (may be out of date):"


@dataclass
class ElementCost:
    element: str
    tokens: int
    share: float


def audit(hits: list[Hit], header: str = HEADER, precision: str = "year") -> list[ElementCost]:
    """TODO: every element of the context, priced -- header included.

    Return an ElementCost per element with its token count and its share of
    the total. The header is an element like any other.
    """
    raise NotImplementedError("implement audit")


def floor_for(hits: list[Hit], header: str, precision: str = "year") -> int:
    """The smallest budget that could hold these hits. Derived, never written down."""
    return estimate_tokens(header) + sum(estimate_tokens(render(h, precision)) for h in hits)


def main() -> None:
    from memlab.app.chat import ask, ingest
    from memlab.eval.exam import QUESTION, exam_from_context
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    NEEDED = ("works at Calico", "does not eat meat", "eats fish", "gluten")
    scope = Scope(user="priya")
    pipeline = at("I7")
    store = JsonlStore("/tmp/memlab-value.jsonl")
    store.clear()
    ingest(store, scope, pipeline)
    pipeline.vectors.index(store.all())
    _ctx, hits = ask(store, scope, QUESTION, k=5, pipeline=pipeline)

    print("every element of the context, priced (full header, dated lines):\n")
    print(f"  {'element':<44}{'tokens':>8}{'share':>8}")
    for cost in audit(hits, HEADER, precision="dated"):
        print(f"  {cost.element:<44}{cost.tokens:>8}{cost.share:>7.0%}")

    print(f"\n  full header:    {estimate_tokens(HEADER)} tokens")
    print(f"  compact header: {estimate_tokens(COMPACT_HEADER)} tokens\n")

    print(f"  {'budget':>7}{'before I8':>11}{'after':>8}")
    for budget in (80, 67, 60, 55, 52, 50):
        before = exam_from_context(store.all(), scope, k=5,
                                   pipeline=at("I7"), budget=budget).is_correct
        after = exam_from_context(store.all(), scope, k=5,
                                  pipeline=at("I8"), budget=budget).is_correct
        print(f"  {budget:>7}{'PASS' if before else 'fail':>11}{'PASS' if after else 'fail':>8}")

    needed = [h for h in hits if any(n in h.memory.content for n in NEEDED)]
    floor = floor_for(needed, COMPACT_HEADER)
    padding = next(h for h in hits if "staff engineer" in h.memory.content)
    print("\n  reached:  52 tokens")
    print(f"  floor:    {floor} tokens")
    print(f"  the gap:  {padding.memory.content!r}, which the packer cannot know is redundant")


if __name__ == "__main__":
    main()
