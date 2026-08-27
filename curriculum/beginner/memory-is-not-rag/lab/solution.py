"""Reference solution: the entire RAG read path, in about ten lines."""
from __future__ import annotations

from memlab.fixtures import load_turns
from memlab.llm.fake import cosine, embed_text

QUESTION = "where do I work and what should I not eat?"
ASKED_IN_SESSION = 14


def history(turns: list[dict] | None = None) -> list[dict]:
    """Everything Priya said BEFORE she asked the question.

    Session 14 is the query, not a memory. Leaving it in the searchable set
    makes the question retrieve itself at 0.650 -- a useful thing to see once,
    and a reminder that "what is in the index" is a design decision, not a given.
    """
    turns = turns if turns is not None else load_turns()
    return [t for t in turns if t["role"] == "user" and t["session"] < ASKED_IN_SESSION]


def retrieve_topk(question: str, turns: list[dict], k: int = 4) -> list[tuple[float, dict]]:
    """Chunk, embed, rank, return top-k. This is a RAG pipeline, complete."""
    q = embed_text(question)
    scored = [(cosine(q, embed_text(t["text"])), t) for t in turns]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:k]
