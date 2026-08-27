"""Reference solution."""
from __future__ import annotations

from memlab.assemble.simple import estimate_tokens


def fit_to_budget(turns: list[dict], budget: int, newest_first: bool = False) -> list[dict]:
    """Pack whole turns until the budget runs out. Never split a turn."""
    ordered = sorted(turns, key=lambda t: t["ts"], reverse=newest_first)
    kept, used = [], 0
    for t in ordered:
        cost = estimate_tokens(t["text"])
        if used + cost > budget:
            break
        kept.append(t)
        used += cost
    return sorted(kept, key=lambda t: t["ts"])
