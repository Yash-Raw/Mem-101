"""Reference solution."""
from __future__ import annotations

from memlab.eval.extraction import NATURAL_QUERY, REQUIRED_STATES, ExtractionScore
from memlab.extract.gate import passes
from memlab.retrieve.embedding import EmbeddingRetriever
from memlab.types import Memory, MemoryType, Scope


def score(
    memories: list[Memory],
    turns: dict[str, str] | None = None,
    scope: Scope | None = None,
    k: int = 10,
) -> ExtractionScore:
    turns = turns or {}
    scope = scope or Scope(user="priya")
    semantic = [m for m in memories if m.type is MemoryType.SEMANTIC and m.is_live]
    retriever = EmbeddingRetriever()

    found, reached = {}, {}
    for name, keys in REQUIRED_STATES.items():
        found[name] = any(any(key in m.content for key in keys) for m in semantic)
        hits = retriever.search(NATURAL_QUERY[name], memories, scope, k=k, live_only=True)
        reached[name] = next(
            (i for i, h in enumerate(hits, 1) if any(key in h.memory.content for key in keys)),
            None,
        )

    over = [m.content for m in memories
            if not passes(m, turns.get(m.provenance.source_id, ""))]

    return ExtractionScore(
        total=len(memories),
        state_recall=sum(found.values()) / len(found),
        reachability=sum(r is not None for r in reached.values()) / len(reached),
        found=found,
        reached=reached,
        over_extracted=over,
    )


def score_profiles(k: int = 10) -> dict[str, ExtractionScore]:
    from memlab.app.chat import ingest
    from memlab.fixtures import load_turns
    from memlab.pipeline import at, get
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    turns = {f"s{t['session']}:{t['ts']}": t["text"] for t in load_turns(user_only=True)}
    out = {}
    for name in ("beginner", "intermediate"):
        store = JsonlStore(f"/tmp/memlab-quality-{name}.jsonl")
        store.clear()
        ingest(store, scope, get(name) if name == "beginner" else at("I1"))
        out[name] = score(store.all(), turns, scope, k=k)
    return out
