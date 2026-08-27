"""Lab: wire it together and prove it persists.

    uv run python curriculum/beginner/your-first-memory-layer/lab/lab.py
"""
from __future__ import annotations

from memlab.app.chat import ingest
from memlab.fixtures import load_turns
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope


def answer(store: JsonlStore, scope: Scope, question: str, k: int = 5, budget: int = 400) -> str:
    """TODO: retrieve scoped to `scope`, then assemble within `budget`."""
    raise NotImplementedError("implement answer")


def restart_check(path, scope: Scope, question: str) -> tuple[bool, int]:
    """Prove persistence is real: a NEW store object over the same file.

    Returns (recall_is_identical, memories_written_by_a_second_ingest).
    """
    first = answer(JsonlStore(path), scope, question)
    fresh = JsonlStore(path)
    second = answer(fresh, scope, question)
    rewritten = ingest(fresh, scope)
    return first == second, rewritten


QUESTIONS = [
    "what should I not eat?",
    "where do I work?",
    "who is Sam?",
    "how do I write my weekly report?",
]


def main() -> None:
    scope = Scope(user="priya")
    path = "/tmp/memlab-v01.jsonl"
    store = JsonlStore(path)
    store.clear()

    written = ingest(store, scope)
    turns = [t for t in load_turns(user_only=True) if t["session"] < 14]
    print(f"ingested {len(turns)} turns -> {written} memories\n")

    for q in QUESTIONS:
        print(f"Q: {q}")
        print((answer(store, scope, q) or "(nothing recalled)").replace("\n", "\n   "))
        print()

    identical, rewritten = restart_check(path, scope, QUESTIONS[0])
    print(f"restart: recall identical = {identical}, second ingest wrote {rewritten}")
    print("\nIt remembers a person across process boundaries. It is also wrong")
    print("in seven specific ways -- which is the next lesson.")


if __name__ == "__main__":
    main()
