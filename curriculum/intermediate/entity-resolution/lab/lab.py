"""Lab: block, score, merge -- and when to run it.

    uv run python curriculum/intermediate/entity-resolution/lab/lab.py
"""
from __future__ import annotations

from dataclasses import replace

from memlab.entity.aliases import mentions, proper_names
from memlab.entity.resolve import MERGE_THRESHOLD, canonical_id
from memlab.entity.resolve import resolve_all as _resolve_all
from memlab.types import Memory


def block_key(surface: str) -> str:
    """TODO: a cheap partition key -- only forms sharing it are compared."""
    raise NotImplementedError("implement block_key")


def score(a: str, b: str) -> float:
    """TODO: how likely are these the same person?

    Prefix agreement should dominate: diminutives and full forms share their
    opening, unrelated names rarely do. Aim for a wide gap between the two
    cases rather than a precisely tuned number.
    """
    raise NotImplementedError("implement score")


def cluster(surface_forms: set[str], threshold: float = MERGE_THRESHOLD) -> dict[str, str]:
    blocks: dict[str, list[str]] = {}
    for form in surface_forms:
        blocks.setdefault(block_key(form), []).append(form)

    assignments: dict[str, str] = {}
    for members in blocks.values():
        groups: list[set[str]] = []
        for form in sorted(members):
            for group in groups:
                if any(score(form, other) >= threshold for other in group):
                    group.add(form)
                    break
            else:
                groups.append({form})
        for group in groups:
            cid = canonical_id(group)
            for form in group:
                assignments[form] = cid
    return assignments


def resolve_all(memories: list[Memory]) -> list[Memory]:
    return _resolve_all(memories)


def resolve_incrementally(memories: list[Memory]) -> list[Memory]:
    """The wrong way, kept for contrast.

    Resolves each memory against only what came before it -- which is exactly
    what a per-turn `resolve` hook does, and it gives one person two ids.
    """
    out: list[Memory] = []
    for memory in memories:
        forms = {f for m in [*out, memory] for f in mentions(m.content)}
        assignments = cluster(forms)
        ids = {assignments[f] for f in mentions(memory.content) if f in assignments}
        out.append(replace(memory, entities=tuple(sorted(ids))) if ids else memory)
    return out


def entity_ids_for(memories: list[Memory], names: tuple[str, ...]) -> set[str]:
    return {
        e for m in memories
        if any(n in m.content for n in names) or proper_names(m.content)
        for e in m.entities
    }


PARTNER = ("Sam ", "Sam's", "Samira", "Sammy")


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import get
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    print("scores:")
    for a, b in [("Sam", "Samira"), ("Sam", "Sammy"), ("Samira", "Sammy"), ("Sam", "Priya")]:
        print(f"   {score(a, b):.2f}  {a} <-> {b}")

    store = JsonlStore("/tmp/memlab-resolve.jsonl")
    store.clear()
    ingest(store, Scope(user="priya"), get("intermediate"))
    memories = store.all()

    about = [m for m in memories
             if any(n in m.content for n in PARTNER) or m.content.startswith("She")]
    print(f"\nstore-wide resolution ({len(about)} memories about one person):")
    for m in about:
        print(f"   {m.entities!s:<14} {m.content[:50]}")

    whole = {e for m in resolve_all(about) for e in m.entities}
    incremental = {e for m in resolve_incrementally(about) for e in m.entities}
    print(f"\n   store-wide  -> {len(whole)} id(s): {whole}")
    print(f"   incremental -> {len(incremental)} id(s): {incremental}")
    print("\nSame person. The second one asked before the evidence arrived.")


if __name__ == "__main__":
    main()
