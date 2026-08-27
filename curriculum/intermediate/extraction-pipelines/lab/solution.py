"""Reference solution."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime

from memlab.extract.atomise import atomise
from memlab.extract.gate import passes
from memlab.extract.naive import SCHEMA
from memlab.extract.pipeline import build_messages
from memlab.llm.base import LLMClient, get_client
from memlab.types import Memory, MemoryType, Provenance, Scope


def extract(turn: dict, scope: Scope, client: LLMClient | None = None) -> list[Memory]:
    """candidates -> atomise -> gate -> route. One model call, at the front."""
    client = client or get_client()
    raw = client.complete(build_messages(turn["text"]), SCHEMA)
    candidates = json.loads(raw) if isinstance(raw, str) else raw

    provenance = Provenance(
        source_id=f"s{turn['session']}:{turn['ts']}", speaker=turn.get("role", "user")
    )
    happened = datetime.fromisoformat(turn["ts"])

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


@dataclass
class ProfileReport:
    name: str
    total: int
    by_type: dict[str, int]
    calico_state_rank: int | None
    northwind_rank: int
    exam_employer: str | None


def compare_profiles(profiles: tuple[str, ...] = ("beginner", "intermediate")) -> list[ProfileReport]:
    from memlab.app.chat import ingest
    from memlab.eval.exam import exam_answer
    from memlab.pipeline import at, get
    from memlab.retrieve.embedding import EmbeddingRetriever
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    reports = []
    for name in profiles:
        store = JsonlStore(f"/tmp/memlab-cmp-{name}.jsonl")
        store.clear()
        ingest(store, scope, get(name) if name == "beginner" else at("I1"))
        memories = store.all()

        hits = EmbeddingRetriever().search("where do I work?", memories, scope, k=len(memories))
        def rank(needle: str, hits: list = hits) -> int | None:
            return next((i for i, h in enumerate(hits, 1) if needle in h.memory.content), None)

        reports.append(
            ProfileReport(
                name=name,
                total=len(memories),
                by_type={t.value: sum(1 for m in memories if m.type is t) for t in MemoryType},
                calico_state_rank=rank("works at Calico Systems"),
                northwind_rank=rank("at Northwind Labs"),
                exam_employer=exam_answer(memories, scope).employer,
            )
        )
    return reports
