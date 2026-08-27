"""Reference solution."""
from __future__ import annotations

from memlab.retrieve.embedding import EmbeddingRetriever
from memlab.types import Memory, Scope

QUESTION = "where do I work and what should I not eat?"

CONTRADICTIONS = [
    ("Priya does not drink coffee", "three coffees"),
    ("detailed explanations", "shorter answers"),
    ("Priya is vegetarian", "Priya eats fish"),
]


def employer_state(context: str) -> str:
    has_stale, has_current = "Northwind" in context, "Calico" in context
    if has_stale and has_current:
        return "both, ambiguous"
    if has_current:
        return "Calico only"
    if has_stale:
        return "Northwind only"
    return "-"


def contradictions_in_context(context: str) -> int:
    """How many live contradictions this context hands the model."""
    return sum(1 for a, b in CONTRADICTIONS if a in context and b in context)


def sweep_k(
    memories: list[Memory], scope: Scope, ks: list[int]
) -> list[tuple[int, str, list[str], int]]:
    retriever = EmbeddingRetriever()
    rows = []
    for k in ks:
        hits = retriever.search(QUESTION, memories, scope, k=k)
        context = " ".join(h.memory.content for h in hits)
        diet = [d for d in ("meat", "fish", "gluten", "vegetarian") if d in context]
        rows.append((k, employer_state(context), diet, contradictions_in_context(context)))
    return rows
