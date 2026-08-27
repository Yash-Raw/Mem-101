"""Lab: sweep k, and watch it fail to help.

    uv run python curriculum/beginner/retrieval-is-not-enough/lab/lab.py
"""
from __future__ import annotations

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
    """TODO: count how many pairs in CONTRADICTIONS have BOTH sides present."""
    raise NotImplementedError("implement contradictions_in_context")


def sweep_k(
    memories: list[Memory], scope: Scope, ks: list[int]
) -> list[tuple[int, str, list[str], int]]:
    """TODO: for each k, retrieve, join the contents, and report
    (k, employer_state, diet facts present, contradiction count)."""
    raise NotImplementedError("implement sweep_k")


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-sweep.jsonl")
    store.clear()
    ingest(store, scope)

    print(f"Q: {QUESTION}\n")
    print(f"{'k':>3}  {'employer':<18} {'diet':<34} contradictions")
    for k, emp, diet, con in sweep_k(store.all(), scope, [3, 5, 10, 15, 20, 25, 30, 36]):
        print(f"{k:>3}  {emp:<18} {diet!s:<34} {con}")

    print("\nNo row is both correct and unambiguous.")
    print("k is not the broken part.")


if __name__ == "__main__":
    main()
