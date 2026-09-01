#!/usr/bin/env python3
"""Frontmatter schema, id/dirname agreement, and the mandatory lesson sections."""
from __future__ import annotations

import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import Problems, concepts, landscape, lessons, syllabus

STAGES = set(syllabus()["stages"])
LEVELS = {lv["id"] for lv in syllabus()["levels"]}

# capstone_piece is optional: orientation lessons bind no code.
LESSON_REQUIRED = {
    "id", "title", "level", "stage", "estimated_minutes",
    "concepts_taught", "status",
}
# Fixed section order. Uniformity is what makes 84 lessons feel like one book.
LESSON_SECTIONS = [
    "Where this sits",
    "The problem",
    "Why this isn't RAG",
    "Mechanism",
    "Design decisions",
    "Lab",
    "What this adds to the capstone",
    "Failure modes",
    "Check yourself",
    "Connections",
]
DERIVED = {"taught_in", "used_in_capstone"}


def main() -> int:
    p = Problems()

    for d in lessons():
        missing = LESSON_REQUIRED - set(d.meta)
        if missing:
            p.add(d.rel, f"missing frontmatter: {', '.join(sorted(missing))}")
        if d.id != d.path.parent.name:
            p.add(d.rel, f"id '{d.id}' != directory '{d.path.parent.name}' (convention C4)")
        if d.meta.get("level") not in LEVELS:
            p.add(d.rel, f"level '{d.meta.get('level')}' is not a known level")
        if d.meta.get("level") != d.path.parent.parent.name:
            p.add(d.rel, "level does not match the directory it lives in")
        if d.meta.get("stage") not in STAGES:
            p.add(d.rel, f"stage '{d.meta.get('stage')}' is not in syllabus.yml stages")
        for k in DERIVED & set(d.meta):
            if d.meta[k]:
                p.add(d.rel, f"'{k}' is derived by build_graph.py; do not hand-author it")

        heads = re.findall(r"^## (.+)$", d.body, re.MULTILINE)
        want = [s for s in LESSON_SECTIONS
                if not (s == "Why this isn't RAG" and d.meta.get("rag_contrast") == "n/a")]
        if [h for h in heads if h in want] != want:
            got = [h for h in heads if h in want]
            miss = [s for s in want if s not in got]
            if miss:
                p.add(d.rel, f"missing required sections: {', '.join(miss)}")
            else:
                p.add(d.rel, f"sections out of order: {got}")

        # Failure modes must be a real table, not a promise.
        fm = re.search(r"^## Failure modes$(.*?)(?=^## |\Z)", d.body, re.MULTILINE | re.DOTALL)
        if fm and len([r for r in fm.group(1).splitlines() if r.strip().startswith("|")]) < 4:
            p.add(d.rel, "Failure modes needs at least 2 table rows")

    for c in concepts():
        if c.id != c.path.stem:
            p.add(c.rel, f"id '{c.id}' != filename '{c.path.stem}'")
        if c.meta.get("kind") != "concept":
            p.add(c.rel, "kind must be 'concept'")
        if c.meta.get("stage") not in STAGES:
            p.add(c.rel, f"stage '{c.meta.get('stage')}' is not in syllabus.yml stages")
        for k in DERIVED & set(c.meta):
            if c.meta[k]:
                p.add(c.rel, f"'{k}' is derived; do not hand-author it")

    for d in landscape():
        for k in ("last_verified", "category", "volatility"):
            if k not in d.meta:
                p.add(d.rel, f"missing '{k}' (landscape pages must be dated and classified)")
        if d.meta.get("kind") != "landscape":
            p.add(d.rel, "kind must be 'landscape'")

    _check_concept_refs(p)
    return p.report("frontmatter")


# Frontmatter fields that name another concept by id. `contrasts_with` is the
# load-bearing one -- it is the "do not confuse with" edge the atlas draws.
CONCEPT_REFS = {
    "concept": ("contrasts_with", "related"),
    "landscape": ("maps_to_concepts",),
}


def _check_concept_refs(p) -> None:
    """A named concept must exist.

    Nothing checked these, and twelve had rotted: `deletion`, `decay`,
    `invariant` and friends are plausible ids that were never filenames. A
    dangling `contrasts_with` is silently dropped when the graph is built, so
    the relation an author wrote simply does not appear anywhere.
    """
    known = {c.id for c in concepts()}
    for docs, kind in ((concepts(), "concept"), (landscape(), "landscape")):
        for d in docs:
            for field in CONCEPT_REFS[kind]:
                for ref in d.meta.get(field, []) or []:
                    if ref not in known:
                        p.add(d.rel, f"{field}: '{ref}' is not a concept id")


if __name__ == "__main__":
    raise SystemExit(main())
