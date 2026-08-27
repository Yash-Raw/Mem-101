"""A deterministic LLM stand-in.

The embedding is the part that matters. Random vectors would make every
retrieval lab meaningless -- cosine similarity would teach nothing. So `embed`
hashes character trigrams and word tokens into a fixed space: fully
deterministic, no network, no key, and genuinely responsive to overlapping
wording. Related sentences really do score higher than unrelated ones, which is
what lets a lab assert an exact expected ranking.

It is a lexical model, not a semantic one. That limit is deliberate and is the
subject of its own lesson: `embedding-recall` has the learner find the pair it
gets wrong, which is how the course introduces what embeddings cannot represent.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

DIMS = 256
FIXTURES = Path(__file__).resolve().parents[3] / "fixtures"

_WORD = re.compile(r"[a-z0-9']+")
_STOP = frozenset(
    ["a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "i", "you", "he", "she", "it", "we", "they", "my", "your", "his", "her", "its", "our", "their", "of", "to", "in", "on", "at", "for", "with", "and", "or", "but", "if", "then", "than", "that", "this", "these", "those", "do", "does", "did", "have", "has", "had", "me", "him", "them", "am", "as", "by", "from", "so", "not", "no", "yes", "there", "here", "what", "which", "who"]
)


def _bucket(token: str) -> int:
    return int.from_bytes(hashlib.blake2b(token.encode(), digest_size=4).digest(), "big") % DIMS


def _features(text: str) -> dict[str, float]:
    words = _WORD.findall(text.lower())
    feats: dict[str, float] = {}
    for w in words:
        if w in _STOP:
            continue
        feats[f"w:{w}"] = feats.get(f"w:{w}", 0.0) + 1.0
        padded = f"^{w}$"
        for i in range(len(padded) - 2):          # character trigrams
            g = f"c:{padded[i:i + 3]}"
            feats[g] = feats.get(g, 0.0) + 0.34   # subword signal, weighted below words
    return feats


def embed_text(text: str) -> list[float]:
    """Deterministic, L2-normalised, dependency-free."""
    vec = [0.0] * DIMS
    for token, weight in _features(text).items():
        vec[_bucket(token)] += weight
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm else vec


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class FakeLLM:
    """Completions are fixture-backed; embeddings are computed."""

    name = "fake"

    def __init__(self, fixtures: Path | None = None) -> None:
        self._dir = fixtures or FIXTURES
        self._responses: dict[str, object] = {}
        path = self._dir / "llm_responses.json"
        if path.exists():
            self._responses = json.loads(path.read_text())

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [embed_text(t) for t in texts]

    def complete(self, messages: list[dict], schema: dict | None = None) -> str | dict:
        key = self._key(messages, schema)
        if key in self._responses:
            return self._responses[key]
        raise KeyError(
            f"FakeLLM has no fixture for request {key}.\n"
            "Author one with memlab.llm.fake.register_fixture(messages, response, schema) "
            "-- no model call is involved. The course's own fixtures are written by "
            "tools/author_extraction_fixtures.py."
        )

    @staticmethod
    def _key(messages: list[dict], schema: dict | None) -> str:
        blob = json.dumps({"m": messages, "s": schema}, sort_keys=True)
        return hashlib.blake2b(blob.encode(), digest_size=8).hexdigest()


def fixture_key(messages: list[dict], schema: dict | None = None) -> str:
    """Public form of the lookup key, so fixtures can be authored offline."""
    return FakeLLM._key(messages, schema)


def register_fixture(
    messages: list[dict],
    response: object,
    schema: dict | None = None,
    fixtures: Path | None = None,
) -> str:
    """Write a canned response into llm_responses.json without calling a model.

    This is how the course's extraction fixtures are authored: hand-written
    expected output, keyed by the exact request that will look it up. No API key
    is involved at any point, so the fixtures are reviewable in a diff.
    """
    path = (fixtures or FIXTURES) / "llm_responses.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text()) if path.exists() else {}
    key = fixture_key(messages, schema)
    data[key] = response
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return key
