"""Reference solution."""

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
    """Every element of the context, priced."""
    lines = [render(h, precision) for h in hits]
    total = estimate_tokens(header) + sum(estimate_tokens(x) for x in lines)
    out = [ElementCost("header", estimate_tokens(header), estimate_tokens(header) / total)]
    for hit, line in zip(hits, lines):
        cost = estimate_tokens(line)
        out.append(ElementCost(hit.memory.content[:40], cost, cost / total))
    return out


def floor_for(hits: list[Hit], header: str, precision: str = "year") -> int:
    """The smallest budget that could hold these hits. Derived, never written down."""
    return estimate_tokens(header) + sum(estimate_tokens(render(h, precision)) for h in hits)
