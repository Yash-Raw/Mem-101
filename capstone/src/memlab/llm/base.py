"""Provider shim.

Labs default to the deterministic fake so the entire course runs offline, in CI,
and for a learner with no API key. Set MEMLAB_LLM=anthropic to use a real model.
"""
from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    def complete(self, messages: list[dict], schema: dict | None = None) -> str | dict: ...
    def embed(self, texts: list[str]) -> list[list[float]]: ...


def get_client(name: str | None = None) -> LLMClient:
    name = name or os.environ.get("MEMLAB_LLM", "fake")
    if name == "fake":
        from .fake import FakeLLM

        return FakeLLM()
    if name == "anthropic":
        from .anthropic import AnthropicLLM

        return AnthropicLLM()
    raise ValueError(f"unknown MEMLAB_LLM={name!r} (expected 'fake' or 'anthropic')")
