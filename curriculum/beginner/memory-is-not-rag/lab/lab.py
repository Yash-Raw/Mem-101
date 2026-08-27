"""Lab: build the read path you thought you needed, then watch it fail.

You are going to implement a complete RAG pipeline over Priya's conversation
history and point it at the question she asks in session 14:

    "where do I work and what should I not eat?"

Every fact needed to answer correctly is in the corpus. The embeddings are
fine. The ranking is fine. Run it anyway.

    uv run python curriculum/beginner/memory-is-not-rag/lab/lab.py
"""
from __future__ import annotations

from memlab.fixtures import load_turns

QUESTION = "where do I work and what should I not eat?"
ASKED_IN_SESSION = 14


def history(turns: list[dict] | None = None) -> list[dict]:
    """Everything Priya said before she asked. Session 14 is the query, not a memory."""
    turns = turns if turns is not None else load_turns()
    return [t for t in turns if t["role"] == "user" and t["session"] < ASKED_IN_SESSION]


def retrieve_topk(question: str, turns: list[dict], k: int = 4) -> list[tuple[float, dict]]:
    """TODO: return the k turns most similar to `question`, highest score first.

    Steps:
      1. embed the question with embed_text()
      2. score every turn with cosine() against that embedding
      3. sort descending by score, return the top k as (score, turn) pairs
    """
    raise NotImplementedError("implement retrieve_topk")


def main() -> None:
    turns = history()
    hits = retrieve_topk(QUESTION, turns, k=len(turns))

    print(f"Q: {QUESTION}\n")
    print(f"All {len(turns)} candidate memories, ranked:\n")
    for rank, (score, t) in enumerate(hits, 1):
        note = ""
        if "Northwind Labs" in t["text"]:
            note = "  <-- employer, TRUE UNTIL Dec 2025"
        elif "Calico Systems" in t["text"]:
            note = "  <-- employer, TRUE NOW"
        elif "vegetarian" in t["text"]:
            note = "  <-- diet, later refined"
        elif "fish" in t["text"]:
            note = "  <-- diet, the refinement"
        elif "gluten" in t["text"]:
            note = "  <-- diet, an addition"
        print(f"  {rank:>2}. {score:.3f}  s{t['session']:>2}  {t['text'][:56]}{note}")

    print("\nCorrect answer: Calico Systems; avoid meat and gluten; fish is fine.")
    print("Now look at where those four facts actually ranked.")


if __name__ == "__main__":
    main()
