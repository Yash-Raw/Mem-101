"""Lab: importance is not relevance.

    uv run python curriculum/intermediate/salience-scoring/lab/lab.py
"""
from __future__ import annotations

from dataclasses import replace

from memlab.extract.gate import ACTIVITY, EXPLICIT
from memlab.forget.salience import (
    ACTIVITY_PENALTY,
    BASE,
    CORROBORATION_BONUS,
    EXPLICIT_BONUS,
    HEARSAY_PENALTY,
    PROCEDURE_BONUS,
    USE_BONUS,
)
from memlab.llm.fake import cosine, embed_text
from memlab.types import Memory, MemoryType


def score(memory: Memory, turn_text: str = "") -> float:
    """TODO: importance in [0, 1], from the weight table in the lesson.

    Start at BASE. Add EXPLICIT_BONUS if the originating turn carried an
    explicit marker, PROCEDURE_BONUS for a procedure, CORROBORATION_BONUS per
    entry in `derived_from`, USE_BONUS per access. Subtract ACTIVITY_PENALTY
    for a finished activity and HEARSAY_PENALTY below 0.5 authority. Clamp.
    """
    raise NotImplementedError("implement score")


def apply(memories: list[Memory], turns: dict[str, str] | None = None) -> list[Memory]:
    turns = turns or {}
    return [
        replace(m, salience=score(m, turns.get(m.provenance.source_id, "")))
        for m in memories
    ]


def record_use(memories: list[Memory], used_ids: set[str]) -> list[Memory]:
    return [
        replace(m, access_count=m.access_count + 1) if m.id in used_ids else m
        for m in memories
    ]


def rank_with_salience(
    query: str, memories: list[Memory], weight: float
) -> list[tuple[float, Memory]]:
    """The obvious use of the score. Measure it before believing in it."""
    q = embed_text(query)
    scored = [
        (cosine(q, embed_text(m.content)) + weight * m.salience, m)
        for m in memories if m.is_live
    ]
    scored.sort(key=lambda pair: -pair[0])
    return scored


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.eval.exam import QUESTION
    from memlab.fixtures import load_turns
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-salience.jsonl")
    store.clear()
    ingest(store, scope, at("I4"))
    turns = {f"s{t['session']}:{t['ts']}": t["text"] for t in load_turns(user_only=True)}

    scored = apply(store.all(), turns)
    live = [m for m in scored if m.is_live]
    print(f"{len({m.salience for m in live})} distinct salience values "
          f"across {len(live)} live memories\n")
    for m in sorted(live, key=lambda m: -m.salience)[:3]:
        print(f"  {m.salience:.2f}  most important  {m.content[:52]}")
    print()

    print("now feed it to the ranker, which is the obvious thing to do:\n")
    print(f"  {'weight':>7}{'employer rank':>15}   top result")
    for weight in (0.0, 0.2, 0.5):
        ranked = rank_with_salience(QUESTION, scored, weight)
        rank = next(i for i, (_, m) in enumerate(ranked, 1)
                    if m.content == "Priya works at Calico Systems")
        print(f"  {weight:>7}{rank:>15}   {ranked[0][1].content[:44]}")

    print("\nThe correct answer sinks. Importance is not relevance.")


if __name__ == "__main__":
    main()
