"""Scoped semantic retrieval.

The scope filter is not an optimisation. Ranking across users and then hoping
similarity keeps them apart is how memory systems leak between tenants, so the
hard filter runs BEFORE anything is scored -- see `scope-then-rank`.

Everything else here is deliberately plain: embed, cosine, sort, cut. Level 2
replaces it with hybrid ranking.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..llm.base import LLMClient, get_client
from ..llm.fake import cosine
from ..types import Memory, Scope


@dataclass
class Hit:
    memory: Memory
    score: float
    # Which sub-question surfaced this. Set by `scoped.search` after
    # `query-formulation` splits a compound query; budgeting needs the
    # attribution to guarantee every question a share of the tokens.
    query: str | None = None


class EmbeddingRetriever:
    def __init__(self, client: LLMClient | None = None) -> None:
        self.client = client or get_client()
        self._cache: dict[str, list[float]] = {}

    def _vec(self, text: str) -> list[float]:
        if text not in self._cache:
            self._cache[text] = self.client.embed([text])[0]
        return self._cache[text]

    def search(
        self,
        query: str,
        memories: list[Memory],
        scope: Scope,
        k: int = 5,
        live_only: bool = True,
    ) -> list[Hit]:
        candidates = [
            m for m in memories
            if m.scope.matches(scope) and (m.is_live or not live_only)
        ]
        q = self._vec(query)
        hits = [Hit(m, cosine(q, self._vec(m.content))) for m in candidates]
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:k]
