"""Reference solution."""
from __future__ import annotations

from dataclasses import replace
from difflib import SequenceMatcher

from memlab.entity.aliases import mentions, proper_names
from memlab.entity.resolve import MERGE_THRESHOLD, canonical_id
from memlab.entity.resolve import resolve_all as _resolve_all
from memlab.types import Memory


def block_key(surface: str) -> str:
    return surface.lower().strip()[:3]


def score(a: str, b: str) -> float:
    a, b = a.lower(), b.lower()
    if a == b:
        return 1.0
    ratio = SequenceMatcher(None, a, b).ratio()
    shared_prefix = len(a) > 2 and (a.startswith(b[:3]) or b.startswith(a[:3]))
    return max(ratio, 0.75 if shared_prefix else 0.0)


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
