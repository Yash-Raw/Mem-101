"""Reference solution."""
from __future__ import annotations

from memlab.forget.audit import ANSWER_MARKERS, BudgetAudit, tier_census  # noqa: F401
from memlab.types import Memory


def audit_context(hits: list, k: int, store: list[Memory]) -> BudgetAudit:
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
    per_session = len(store) / sessions
    return len(store), round(per_session * horizon)
