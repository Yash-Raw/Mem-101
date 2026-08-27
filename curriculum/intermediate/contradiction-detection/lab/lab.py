"""Lab: the contradiction similarity cannot see.

    uv run python curriculum/intermediate/contradiction-detection/lab/lab.py
"""
from __future__ import annotations

import json
from itertools import combinations

from memlab.evolve.conflict import SCHEMA, Relation, build_messages
from memlab.llm.base import LLMClient, get_client
from memlab.llm.fake import cosine, embed_text
from memlab.types import Memory, MemoryType, Scope

# Pairs whose true relationship we know, for scoring the two generators.
KNOWN = [
    ("Priya is vegetarian", "Priya is pescatarian", "refinement"),
    ("Priya drinks tea", "Priya works at Calico Systems", "NOISE"),
    ("Priya prefers detailed explanations with reasoning",
     "Priya prefers shorter answers", "contradiction"),
    ("Priya does not drink coffee", "Priya drinks three coffees a day", "contradiction"),
    ("Priya is a data engineer at Northwind Labs",
     "Priya works at Calico Systems", "contradiction"),
]


def slot_of(memory: Memory) -> str | None:
    """TODO: which attribute does this claim fill? Use SLOTS. None if no match."""
    raise NotImplementedError("implement slot_of")


def subject_of(memory: Memory, scope: Scope) -> frozenset[str]:
    return frozenset(memory.entities) or frozenset({scope.user})


def candidates(memories: list[Memory], scope: Scope) -> list[tuple[Memory, Memory, str]]:
    """TODO: pairs of live semantic beliefs sharing a subject AND a slot.

    Note what is NOT in this function: any similarity score. That is the point
    of the lesson -- the pair that matters most scores 0.285.
    """
    raise NotImplementedError("implement candidates")


def classify(a: Memory, b: Memory, client: LLMClient | None = None) -> Relation:
    client = client or get_client()
    raw = client.complete(build_messages(a.content, b.content), SCHEMA)
    payload = json.loads(raw) if isinstance(raw, str) else raw
    return Relation(payload["relation"])


def known_similarities() -> list[tuple[float, str, str, str]]:
    scored = [
        (cosine(embed_text(a), embed_text(b)), a, b, label) for a, b, label in KNOWN
    ]
    return sorted(scored, reverse=True, key=lambda t: t[0])


def similarity_candidates(
    memories: list[Memory], scope: Scope, threshold: float
) -> list[tuple[Memory, Memory]]:
    """The generator this lesson rejects, for measuring what it would cost."""
    beliefs = [m for m in memories if m.type is MemoryType.SEMANTIC and m.is_live]
    vectors = {m.id: embed_text(m.content) for m in beliefs}
    return [
        (a, b) for a, b in combinations(beliefs, 2)
        if subject_of(a, scope) == subject_of(b, scope)
        and cosine(vectors[a.id], vectors[b.id]) >= threshold
    ]


def main() -> None:
    from collections import Counter

    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-conflict.jsonl")
    store.clear()
    ingest(store, scope, at("I3"))
    memories = store.all()

    print("pairs whose true relationship we know, by similarity:\n")
    for score, a, b, label in known_similarities():
        flag = "  <-- THE ONE THAT MATTERS" if label == "contradiction" and "Northwind" in a else ""
        print(f"  {score:.3f}  [{label:<13}] {a[:34]:<34} | {b[:30]}{flag}")

    cands = candidates(memories, scope)
    sim = similarity_candidates(memories, scope, 0.45)
    print(f"\ncandidate pairs by slot:       {len(cands)}")
    print(f"candidate pairs by similarity: {len(sim)} (at 0.45)")
    has_employer = any("Northwind" in a.content and "Calico" in b.content for a, b in sim)
    print(f"  ...does similarity include the employer pair? {has_employer}")

    relations = Counter(classify(a, b).value for a, b, _ in cands)
    print(f"\nclassified {len(cands)} pairs:")
    for relation, n in relations.most_common():
        print(f"  {relation:<15} {n}")


if __name__ == "__main__":
    main()
