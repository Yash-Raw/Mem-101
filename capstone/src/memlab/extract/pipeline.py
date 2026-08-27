"""Staged extraction.

Beginner's extractor was one prompt and one decision: what did they say? This
adds the stage that decision was missing -- **if the turn describes a change,
also record the state it produced.**

That single instruction is the fix for the course's headline failure. Session 8
says "I'm leaving Northwind. Starting at Calico Systems in January", which is an
event; the question asks "where do I work", which wants a state. Beginner stored
only the events, so the correct answer ranked 35th of 36 and nothing downstream
could recover it.

The stages:

    candidates  -> one LLM call per turn (the only model call on this path)
    atomise     -> one fact per record, so it stays updatable
    gate        -> rules: does this earn a durable slot?
    route       -> assign the type that governs its lifecycle

Only the first stage calls a model. The gate is rules on purpose: it keeps the
write path cheap, auditable, and -- because FakeLLM keys on the request -- keeps
the fixture tables hand-authorable.
"""
from __future__ import annotations

import json
from datetime import datetime

from ..llm.base import LLMClient, get_client
from ..types import Memory, MemoryType, Provenance, Scope
from .atomise import atomise
from .gate import passes
from .naive import SCHEMA

PROMPT = (
    "Extract durable facts worth remembering from the user's message. "
    "Return a JSON array of objects with 'content' and 'type'. "
    "Types: semantic (a lasting fact or preference), episodic (something that "
    "happened at a time), procedural (how to do something). "
    "Write each fact as a standalone statement. "
    "IMPORTANT: if the message describes a CHANGE, record both the event and "
    "the resulting state. 'I'm moving to Berlin next month' yields the episodic "
    "event and the semantic fact 'Lives in Berlin'. A question about the "
    "present must be answerable without re-reading the event. "
    "Return [] if nothing is durable."
)


def build_messages(text: str) -> list[dict]:
    return [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": text},
    ]


def extract(turn: dict, scope: Scope, client: LLMClient | None = None) -> list[Memory]:
    client = client or get_client()
    raw = client.complete(build_messages(turn["text"]), SCHEMA)
    candidates = json.loads(raw) if isinstance(raw, str) else raw

    happened = datetime.fromisoformat(turn["ts"])
    source = f"s{turn['session']}:{turn['ts']}"
    provenance = Provenance(source_id=source, speaker=turn.get("role", "user"))

    memories = [
        Memory(
            content=fact,
            type=MemoryType(candidate["type"]),
            scope=scope,
            provenance=provenance,
            happened_at=happened,
        )
        for candidate in candidates
        for fact in atomise(candidate["content"], MemoryType(candidate["type"]))
    ]
    return [m for m in memories if passes(m, turn["text"])]
