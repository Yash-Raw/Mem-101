"""Access to the canonical corpus.

Every lab in every level reads the same conversation: Priya, 14 sessions,
March 2025 to August 2026. Reusing one corpus is deliberate -- by the time a
learner reaches belief updating in Intermediate, they are fixing a contradiction
they personally created back in Beginner, in a transcript they already know.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def corpus_path() -> Path:
    return FIXTURES / "corpus.jsonl"


def load_turns(user_only: bool = False) -> list[dict[str, Any]]:
    """The conversation, in order."""
    turns = [
        json.loads(line)
        for line in corpus_path().read_text().splitlines()
        if line.strip()
    ]
    return [t for t in turns if t["role"] == "user"] if user_only else turns


def load_agent_writes() -> list[dict[str, Any]]:
    """Memories written by other agents into shared scope."""
    path = FIXTURES / "agent_writes.jsonl"
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def load_gold() -> dict[str, Any]:
    """Ground truth: the eval answer key, and the index lessons cite."""
    return yaml.safe_load((FIXTURES / "gold.yml").read_text())


def session(n: int) -> list[dict[str, Any]]:
    return [t for t in load_turns() if t["session"] == n]
