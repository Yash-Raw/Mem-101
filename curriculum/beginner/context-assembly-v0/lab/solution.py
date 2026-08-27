"""Reference solution."""
from __future__ import annotations

from memlab.assemble.simple import HEADER, estimate_tokens
from memlab.retrieve.embedding import Hit


def render(hit: Hit) -> str:
    when = hit.memory.happened_at.date().isoformat() if hit.memory.happened_at else "undated"
    return f"- [{when}] {hit.memory.content}"


def assemble(hits: list[Hit], budget_tokens: int = 400) -> str:
    """Pack highest-scoring first. Stop at the budget. Never split a memory."""
    if not hits:
        return ""
    lines, used = [], estimate_tokens(HEADER)
    for h in hits:
        line = render(h)
        cost = estimate_tokens(line)
        if used + cost > budget_tokens:
            break
        lines.append(line)
        used += cost
    return HEADER + "\n" + "\n".join(lines) if lines else ""


def assemble_truncating(hits: list[Hit], budget_tokens: int = 400) -> str:
    """The wrong way, for contrast: cut the last memory to fit exactly."""
    if not hits:
        return ""
    out, used = [HEADER], estimate_tokens(HEADER)
    for h in hits:
        line = render(h)
        cost = estimate_tokens(line)
        if used + cost > budget_tokens:
            room = (budget_tokens - used) * 4
            if room > 0:
                out.append(line[:room])
            break
        out.append(line)
        used += cost
    return "\n".join(out)
