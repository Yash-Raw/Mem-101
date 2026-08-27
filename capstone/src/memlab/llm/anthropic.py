"""The live backend. Optional -- nothing in the course requires it.

Install with `uv sync --extra live` and set MEMLAB_LLM=anthropic. The `anthropic`
import is deliberately inside the methods so the base install stays dependency-free
and importing this module never fails on its own.

Embeddings are NOT provided by this backend: the Anthropic API has no embedding
endpoint, so `embed` delegates to the deterministic local embedder. That is the
honest arrangement rather than a limitation to work around -- it also means
switching backends changes only the extraction quality, so a lab's retrieval
behaviour stays comparable between fake and live runs.
"""
from __future__ import annotations

import json
import os

from .fake import embed_text

MODEL = os.environ.get("MEMLAB_MODEL", "claude-sonnet-5")
MAX_TOKENS = 2048


class AnthropicLLM:
    name = "anthropic"

    def __init__(self, model: str = MODEL) -> None:
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    "the live backend needs the anthropic package: "
                    "uv sync --extra live"
                ) from e
            self._client = anthropic.Anthropic()
        return self._client

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Delegated to the local embedder -- see the module docstring."""
        return [embed_text(t) for t in texts]

    def complete(self, messages: list[dict], schema: dict | None = None) -> str | dict:
        system = " ".join(m["content"] for m in messages if m["role"] == "system")
        turns = [m for m in messages if m["role"] != "system"]

        if schema is not None:
            system += (
                "\n\nRespond with JSON only, matching this schema. "
                "No prose, no code fence.\n" + json.dumps(schema)
            )

        response = self._get_client().messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=system or None,
            messages=turns,
        )
        text = "".join(block.text for block in response.content if block.type == "text")

        if schema is None:
            return text
        try:
            return json.loads(text.strip().removeprefix("```json").removesuffix("```").strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"live backend returned non-JSON for a schema request: {text[:200]}") from e
