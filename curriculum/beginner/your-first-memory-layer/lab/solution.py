"""Reference solution."""
from __future__ import annotations

from memlab.app.chat import ingest
from memlab.assemble.simple import assemble
from memlab.retrieve.embedding import EmbeddingRetriever
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope


def answer(store: JsonlStore, scope: Scope, question: str, k: int = 5, budget: int = 400) -> str:
    """The whole read path, in one function."""
    hits = EmbeddingRetriever().search(question, store.all(), scope, k=k)
    return assemble(hits, budget_tokens=budget)


def restart_check(path, scope: Scope, question: str) -> tuple[bool, int]:
    """Prove persistence is real: a NEW store object over the same file.

    Returns (recall_is_identical, memories_written_by_a_second_ingest).
    """
    first = answer(JsonlStore(path), scope, question)
    fresh = JsonlStore(path)
    second = answer(fresh, scope, question)
    rewritten = ingest(fresh, scope)
    return first == second, rewritten
