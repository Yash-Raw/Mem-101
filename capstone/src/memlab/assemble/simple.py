"""Packing retrieved memories into the prompt.

Two choices here that look cosmetic and are not:

1. Memories are labelled as *recalled beliefs*, not stated as fact. A model
   handed a bare list of assertions will defend them against the user.
2. The budget is enforced by dropping whole memories, never by truncating one.
   Half a fact is worse than no fact -- "Priya is allergic to" is a hazard.
"""
from __future__ import annotations

from ..retrieve.embedding import Hit

HEADER = (
    "Here is what you remember about this user. These are recalled beliefs, "
    "not verified facts, and some may be out of date:"
)


def estimate_tokens(text: str) -> int:
    """Crude on purpose. Real tokenisation arrives with the budget lesson."""
    return max(1, len(text) // 4)


def assemble(hits: list[Hit], budget_tokens: int = 400) -> str:
    """Pack highest-scoring first, stop at the budget, never split a memory."""
    if not hits:
        return ""

    lines: list[str] = []
    used = estimate_tokens(HEADER)
    for h in hits:
        when = h.memory.happened_at.date().isoformat() if h.memory.happened_at else "undated"
        line = f"- [{when}] {h.memory.content}"
        cost = estimate_tokens(line)
        if used + cost > budget_tokens:
            break
        lines.append(line)
        used += cost

    return HEADER + "\n" + "\n".join(lines) if lines else ""
