"""Naive extraction: turns into facts.

Deliberately missing everything Intermediate adds. There is no deduplication,
no entity resolution, no conflict detection, and no salience gate. Every
candidate the model returns becomes a memory.

That is not a strawman -- it is what "add memory to your agent" usually means,
and it works well enough to feel finished. The failures it produces are the
subject of `watching-it-fail`.
"""
from __future__ import annotations

import json
from datetime import datetime

from ..llm.base import LLMClient, get_client
from ..types import Memory, MemoryType, Provenance, Scope

SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "type": {"enum": [t.value for t in MemoryType]},
        },
        "required": ["content", "type"],
    },
}

PROMPT = (
    "Extract durable facts worth remembering from the user's message. "
    "Return a JSON array of objects with 'content' and 'type'. "
    "Types: semantic (a lasting fact or preference), episodic (something that "
    "happened at a time), procedural (how to do something). "
    "Write each fact as a standalone statement. Return [] if nothing is durable."
)


def build_messages(text: str) -> list[dict]:
    return [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": text},
    ]


def extract(
    turn: dict,
    scope: Scope,
    client: LLMClient | None = None,
) -> list[Memory]:
    """One turn in, zero or more memories out."""
    client = client or get_client()
    raw = client.complete(build_messages(turn["text"]), SCHEMA)
    candidates = json.loads(raw) if isinstance(raw, str) else raw

    recorded = datetime.fromisoformat(turn["ts"])
    happened = datetime.fromisoformat(turn["ts"])
    source = f"s{turn['session']}:{turn['ts']}"

    return [
        Memory(
            content=c["content"],
            type=MemoryType(c["type"]),
            scope=scope,
            provenance=Provenance(source_id=source, speaker=turn.get("role", "user")),
            happened_at=happened,
            recorded_at=recorded,
        )
        for c in candidates
    ]
