"""Lab: what happens at the budget line.

    uv run python curriculum/beginner/context-assembly-v0/lab/lab.py
"""
from __future__ import annotations

from memlab.assemble.simple import HEADER, estimate_tokens
from memlab.retrieve.embedding import Hit


def render(hit: Hit) -> str:
    when = hit.memory.happened_at.date().isoformat() if hit.memory.happened_at else "undated"
    return f"- [{when}] {hit.memory.content}"


def assemble(hits: list[Hit], budget_tokens: int = 400) -> str:
    """TODO: pack highest-scoring first, stop at the budget, never split a memory.

    Start the budget with the cost of HEADER itself -- it is not free.
    Return "" if nothing fits.
    """
    raise NotImplementedError("implement assemble")


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


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.retrieve.embedding import EmbeddingRetriever
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-assemble.jsonl")
    store.clear()
    ingest(store, scope)
    hits = EmbeddingRetriever().search(
        "where do I work and what should I not eat?", store.all(), scope, k=8
    )

    for budget in (40, 60, 200):
        text = assemble(hits, budget)
        n = text.count("\n- ")
        print(f"\n=== budget {budget} tokens -> {n} memories, {estimate_tokens(text)} used")
        print(text or "(nothing fits)")

    print("\n=== the truncating variant at 60 tokens")
    print(assemble_truncating(hits, 60))
    print("\nLook at its last line.")


if __name__ == "__main__":
    main()
