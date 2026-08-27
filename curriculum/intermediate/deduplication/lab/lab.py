"""Lab: the duplicate idempotency could not see.

    uv run python curriculum/intermediate/deduplication/lab/lab.py
"""
from __future__ import annotations

from itertools import combinations

from memlab.evolve.dedupe import DUPLICATE_THRESHOLD, Merge
from memlab.llm.fake import cosine, embed_text
from memlab.types import Memory

NEAR_MISSES = [
    ("was diagnosed with a gluten", "has a gluten intolerance"),
    ("is leaving Northwind Labs", "left Northwind Labs last month"),
    ("Priya is vegetarian", "Priya is pescatarian"),
]


def _eligible(a: Memory, b: Memory) -> bool:
    """TODO: can these two even BE duplicates?

    Same type matters most -- an event and the state it produced score high and
    are doing different jobs. Also: both live, same user, same entities.
    """
    raise NotImplementedError("implement _eligible")


def duplicate_pairs(
    memories: list[Memory], threshold: float = DUPLICATE_THRESHOLD
) -> list[Merge]:
    vectors = {m.id: embed_text(m.content) for m in memories}
    found = []
    for a, b in combinations(memories, 2):
        if not _eligible(a, b):
            continue
        score = cosine(vectors[a.id], vectors[b.id])
        if score >= threshold:
            first, second = sorted((a, b), key=lambda m: (m.happened_at or m.recorded_at))
            found.append(Merge(kept=first, dropped=second, similarity=score))
    return found


def dedupe(memories: list[Memory]) -> list[Memory]:
    """TODO: drop the duplicates, and raise confidence on what survives.

    An independent restatement is evidence -- it is the one thing a merge
    produces rather than destroys.
    """
    raise NotImplementedError("implement dedupe")


def near_miss_scores(memories: list[Memory]) -> list[tuple[float, str, str]]:
    """The pairs a lower threshold would wrongly collapse."""
    out = []
    for left, right in NEAR_MISSES:
        a = next((m for m in memories if left in m.content), None)
        b = next((m for m in memories if right in m.content), None)
        if a and b:
            out.append((cosine(embed_text(a.content), embed_text(b.content)),
                        a.content, b.content))
    return sorted(out, reverse=True)


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    # The store as I2 left it -- resolved, not yet deduplicated.
    store = JsonlStore("/tmp/memlab-dedupe.jsonl")
    store.clear()
    ingest(store, Scope(user="priya"), at("I2"))
    memories = store.all()

    merges = duplicate_pairs(memories)
    print(f"{len(merges)} merge(s) in {len(memories)} memories:\n")
    for m in merges:
        print(f"  {m.similarity:.3f}  {m.reason}")
        print(f"     keep  {m.kept.content!r}  from {m.kept.provenance.source_id}")
        print(f"     drop  {m.dropped.content!r}  from {m.dropped.provenance.source_id}")

    after = dedupe(memories)
    print(f"\n{len(memories)} -> {len(after)} memories")

    print("\nnear-misses a lower threshold would collapse:")
    for score, a, b in near_miss_scores(after):
        print(f"  {score:.3f}  {a[:38]:<38} | {b[:38]}")
    print("\nAll survive. Each one is a relationship, not a repetition.")


if __name__ == "__main__":
    main()
