#!/usr/bin/env python3
"""Enforce the seven graph invariants.

The important one is #4: the linear order in syllabus.yml must be a valid
topological sort of the prerequisite DAG declared in lesson frontmatter.
That check is what makes the level split provable instead of aspirational.
"""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import Problems, concepts, landscape, lessons, syllabus_lessons


def main() -> int:
    p = Problems()
    ls = lessons()
    if not ls:
        print("  ok  graph (no lessons authored yet)")
        return 0

    by_id = {d.id: d for d in ls}
    concept_ids = {c.id for c in concepts()}
    landscape_ids = {d.id for d in landscape()}

    order = [l["id"] for _, _, l in syllabus_lessons()]
    position = {lid: i for i, lid in enumerate(order)}

    taught: dict[str, list[str]] = {}
    for d in ls:
        for c in d.meta.get("concepts_taught", []) or []:
            taught.setdefault(c, []).append(d.id)

    for d in ls:
        req_l = d.meta.get("lessons_required", []) or []
        req_c = d.meta.get("concepts_required", []) or []

        # 1 / 7 — referenced things exist, and landscape is never a prerequisite
        for r in req_l:
            if r in landscape_ids:
                p.add(d.rel, f"landscape page '{r}' used as a prerequisite (quarantine violation)")
            elif r not in by_id:
                p.add(d.rel, f"lessons_required '{r}' has no lesson")
        for c in req_c + (d.meta.get("concepts_taught", []) or []):
            if c not in concept_ids:
                p.add(d.rel, f"concept '{c}' has no page in concepts/")

        # lesson must be in the syllabus at all
        if d.id not in position:
            p.add(d.rel, "lesson is not listed in curriculum/syllabus.yml")
            continue

        # 4 — linear order respects the DAG
        for r in req_l:
            if r in position and position[r] >= position[d.id]:
                p.add(d.rel, f"requires '{r}', which comes later in syllabus.yml")

        # 6 — a concept must be taught before it is required
        for c in req_c:
            first = min((position[t] for t in taught.get(c, []) if t in position), default=None)
            if first is None:
                p.add(d.rel, f"requires concept '{c}', which no lesson teaches")
            elif first >= position[d.id]:
                p.add(d.rel, f"requires concept '{c}', first taught later in the course")

    # 3 — the DAG is acyclic
    state: dict[str, int] = {}

    def walk(node: str, trail: list[str]) -> None:
        if state.get(node) == 2:
            return
        if state.get(node) == 1:
            cyc = trail[trail.index(node):] + [node]
            p.add("syllabus", "prerequisite cycle: " + " -> ".join(cyc))
            return
        state[node] = 1
        for r in by_id.get(node, None).meta.get("lessons_required", []) or [] if node in by_id else []:
            if r in by_id:
                walk(r, trail + [node])
        state[node] = 2

    for d in ls:
        walk(d.id, [])

    # 2 — no orphan concepts
    for c in concepts():
        if c.meta.get("status") == "stub":
            continue
        if c.id not in taught:
            p.add(c.rel, "concept page is never taught by any lesson (orphan)")

    # 5 — every authored lesson is reachable from the first
    if order:
        reachable = {order[0]}
        for lid in order:
            if lid in by_id and (set(by_id[lid].meta.get("lessons_required", []) or []) & reachable
                                 or not (by_id[lid].meta.get("lessons_required") or [])):
                reachable.add(lid)
        for d in ls:
            if d.id not in reachable:
                p.add(d.rel, "lesson is unreachable from the course entry point")

    return p.report("graph")


if __name__ == "__main__":
    raise SystemExit(main())
