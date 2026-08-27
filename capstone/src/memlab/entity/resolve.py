"""Deciding which mentions denote the same person.

Three stages, and the middle one is where the judgement lives:

    block   cheap partition, so scoring is not quadratic over the whole store
    score   how likely are these two surface forms the same entity?
    merge   above threshold, assign a shared canonical id

Resolution **links; it does not rewrite**. The `entities` field gains a
canonical id and `content` is left exactly as spoken. Rewriting "Sammy" to
"Samira" inside a memory would destroy the record of what was actually said,
and provenance is the thing that makes deletion and audit possible later.

Because `Memory.id` is derived from content, scope, type and source -- not from
entities -- linking never changes a memory's identity. Resolution can be re-run.
"""
from __future__ import annotations

from dataclasses import replace
from difflib import SequenceMatcher

from ..types import Memory
from .aliases import PRONOUNS, descriptors, leading_pronoun, mentions, proper_names

MERGE_THRESHOLD = 0.55
PRONOUN_IDS = frozenset(PRONOUNS)


def block_key(surface: str) -> str:
    """Cheap partition. Only forms sharing a key are ever compared."""
    return surface.lower().strip()[:3]


def score(a: str, b: str) -> float:
    """How likely are these the same person?

    Prefix agreement dominates, because diminutives and full forms share their
    opening ("Sam" / "Samira" / "Sammy") while unrelated names rarely do.
    """
    a, b = a.lower(), b.lower()
    if a == b:
        return 1.0
    ratio = SequenceMatcher(None, a, b).ratio()
    shared_prefix = len(a) > 2 and (a.startswith(b[:3]) or b.startswith(a[:3]))
    return max(ratio, 0.75 if shared_prefix else 0.0)


def canonical_id(surface_forms: set[str]) -> str:
    """The longest proper name in the cluster, slugified. Stable across runs."""
    names = sorted((s for s in surface_forms if s[:1].isupper()), key=len, reverse=True)
    chosen = names[0] if names else min(surface_forms)
    return chosen.lower().replace(" ", "-")


def cluster(surface_forms: set[str], threshold: float = MERGE_THRESHOLD) -> dict[str, str]:
    """surface form -> canonical id."""
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
    """Link every memory to the canonical entities it mentions.

    This runs over the WHOLE store, not per turn, and that is not an
    optimisation -- it is a correctness requirement. Resolved incrementally,
    "Sam" in session 2 clusters alone and gets the canonical id `sam`; when
    "Samira" arrives in session 3 the cluster's best name changes and the id
    should have been `samira`. The early memories are then linked to an id
    nothing else uses, which is the split problem arriving by the back door.

    An entity's canonical form depends on evidence that has not arrived yet, so
    resolution either sees everything or must be re-run. It belongs in the
    consolidation stage for exactly that reason.
    """
    pool = list(memories)
    forms = {m for memory in pool for m in mentions(memory.content)}
    assignments = cluster(forms)

    # A descriptor and the name it appears beside denote one person. "My
    # partner Sam is a nurse" is the sentence that binds them, and without it
    # "my partner" would cluster alone forever.
    for memory in pool:
        names = proper_names(memory.content)
        descs = descriptors(memory.content)
        if names and descs:
            target = assignments.get(names[0])
            for d in descs:
                if target:
                    assignments[d] = target

    linked = []
    for memory in pool:
        found = mentions(memory.content)
        ids = {assignments[f] for f in found if f in assignments}

        # A memory that opens with a bare pronoun has no antecedent of its own.
        # Inherit from the nearest earlier memory in the same session that
        # named someone -- crude, and it is exactly what coreference means here.
        # A pronoun never becomes an entity in its own right.
        if leading_pronoun(memory.content):
            ids = {i for i in ids if i not in PRONOUN_IDS}
            ids |= _antecedent(memory, pool, assignments)

        linked.append(replace(memory, entities=tuple(sorted(ids))) if ids else memory)
    return linked


def _antecedent(memory: Memory, pool: list[Memory], assignments: dict[str, str]) -> set[str]:
    session = memory.provenance.source_id.split(":")[0]
    earlier = [
        m for m in pool
        if m.provenance.source_id.split(":")[0] == session
        and m.recorded_at <= memory.recorded_at
        and proper_names(m.content)
    ]
    if not earlier:
        return set()
    names = proper_names(earlier[-1].content)
    return {assignments[n] for n in names if n in assignments}
