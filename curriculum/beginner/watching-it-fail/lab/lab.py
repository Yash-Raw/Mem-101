"""Lab: measure all seven failures on your own store.

    uv run python curriculum/beginner/watching-it-fail/lab/lab.py
"""
from __future__ import annotations

from dataclasses import dataclass

from memlab.retrieve.embedding import EmbeddingRetriever
from memlab.types import Memory, Scope

QUESTION = "where do I work and what should I not eat?"


@dataclass
class Finding:
    n: int
    name: str
    evidence: str
    fixed_by: str


def rank_of(ranked, needle: str) -> int | None:
    return next((i for i, h in enumerate(ranked, 1) if needle in h.memory.content), None)


def diagnose(memories: list[Memory], scope: Scope) -> list[Finding]:
    """TODO: return one Finding per failure, in the order the lesson lists them.

    Each Finding needs EVIDENCE computed from the store -- a rank, a count, a
    set of values -- not a description. "staleness is a problem" is not a
    finding; "the dead employer ranks 9 of 36 and the live one ranks 35" is.

    Useful: rank_of(ranked, needle), the contents list, and the fact that
    every memory carries .salience, .access_count and .is_live.
    """
    raise NotImplementedError("implement diagnose")

def wrong_answers(memories: list[Memory], scope: Scope, k: int = 10) -> list[str]:
    """Which of the four documented wrong answers this store can produce."""
    hits = EmbeddingRetriever().search(QUESTION, memories, scope, k=k)
    text = " ".join(h.memory.content for h in hits)
    wrong = []
    if "Northwind" in text:
        wrong.append("says Northwind Labs (stale employer recalled)")
    if "Priya is vegetarian" in text and "Priya eats fish" not in text:
        wrong.append("says avoid fish (refinement never applied)")
    if "gluten" not in text:
        wrong.append("omits gluten (diet facts collapsed)")
    if "Berlin" in text:
        wrong.append("says Berlin (hearsay promoted to fact)")
    return wrong


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-diagnose.jsonl")
    store.clear()
    ingest(store, scope)
    memories = store.all()

    print(f"diagnosing {len(memories)} memories\n")
    for f in diagnose(memories, scope):
        print(f"  {f.n}. {f.name}")
        print(f"     evidence: {f.evidence}")
        print(f"     fixed by: {f.fixed_by}\n")

    print(f"the exam -- {QUESTION!r}")
    print("  correct: Calico Systems; avoid meat and gluten; fish is fine\n")
    for w in wrong_answers(memories, scope):
        print(f"  WRONG: {w}")


if __name__ == "__main__":
    main()
