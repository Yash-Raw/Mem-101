"""Does this element earn its tokens?

The context is not a list of memories. It is a list of memories *plus* framing,
and the framing is charged at the same rate.

    Here is what you remember about this user. These are recalled beliefs,
    not verified facts, and some may be out of date:

That header is **29 tokens against an 80-token context -- 36%**, and it is not
waste. `context-assembly-v0` measured what it buys: under an assertive framing
a model defends a stale fact against the user correcting it; under this one it
updates. It is the cheapest reliability improvement in the system.

Both things are true, and "does it help?" is therefore the wrong question. The
question is **what does it cost, and what is it displacing** -- and at a tight
budget it is displacing a dietary restriction.

Right-sizing it to 11 tokens keeps the belief framing and returns 18 tokens:
enough for one more fact, which is exactly the fact that was being dropped.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..retrieve.embedding import Hit
from .ordering import render
from .simple import HEADER, estimate_tokens

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
