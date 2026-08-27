"""What not forgetting actually costs.

The argument for forgetting is usually made about storage, which is the one
resource that is cheap. The real costs are per-*retrieval* and they compound:
every memory is embedded once and then ranked on every query forever, competing
for a token budget that does not grow with the store.

So the measurement that matters is not "how big is the store" but **"how much
of what the model sees is doing any work"**.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..types import Memory, Tier

# The claims the session-14 question actually needs, by content marker.
ANSWER_MARKERS = ("works at Calico", "does not eat meat", "gluten", "eats fish")


@dataclass
class BudgetAudit:
    slots: int
    useful: int
    wasted_contents: list[str]
    store_size: int
    live: int

    @property
    def waste(self) -> float:
        return len(self.wasted_contents) / self.slots if self.slots else 0.0


def audit_context(hits: list, k: int, store: list[Memory]) -> BudgetAudit:
    """How many of the k slots carried a claim the answer needed?"""
    contents = [h.memory.content for h in hits[:k]]
    useful = [c for c in contents if any(m in c for m in ANSWER_MARKERS)]
    return BudgetAudit(
        slots=len(contents),
        useful=len(useful),
        wasted_contents=[c for c in contents if c not in useful],
        store_size=len(store),
        live=sum(1 for m in store if m.is_live),
    )


def projected_growth(store: list[Memory], sessions: int, horizon: int) -> tuple[int, int]:
    """(today, at horizon) memories, at the rate this corpus actually produced.

    Storage is the cheap part; this number matters because every one of them
    is ranked on every query.
    """
    per_session = len(store) / sessions
    return len(store), round(per_session * horizon)


def tier_census(store: list[Memory]) -> dict[str, int]:
    return {
        t.value: sum(1 for m in store if m.is_live and m.tier is t) for t in Tier
    }
