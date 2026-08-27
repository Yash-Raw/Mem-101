#!/usr/bin/env python3
"""Derive the concept graph from frontmatter and inject it back into the pages.

Edges are declared in frontmatter only — never in a separate graph file that
would drift. Everything between <!-- graph:begin --> and <!-- graph:end --> is
generated; --check fails CI when a block is stale or hand-edited.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import ROOT, concepts, lessons, syllabus_lessons

BLOCK = re.compile(r"(<!--\s*graph:begin\s*-->)(.*?)(<!--\s*graph:end\s*-->)", re.DOTALL)
GRAPH_JSON = ROOT / "concepts" / "graph.json"


def build() -> dict:
    ls = lessons()
    by_id = {d.id: d for d in ls}
    order = [l["id"] for _, _, l in syllabus_lessons()]
    pos = {lid: i for i, lid in enumerate(order)}

    taught: dict[str, list[str]] = {}
    used: dict[str, list[str]] = {}
    for d in ls:
        for c in d.meta.get("concepts_taught", []) or []:
            taught.setdefault(c, []).append(d.id)
        for c in d.meta.get("concepts_required", []) or []:
            used.setdefault(c, []).append(d.id)

    unlocks: dict[str, list[str]] = {}
    for d in ls:
        for r in d.meta.get("lessons_required", []) or []:
            unlocks.setdefault(r, []).append(d.id)

    nodes = [
        {"id": d.id, "type": "lesson", "title": d.meta["title"], "level": d.meta["level"],
         "stage": d.meta["stage"], "order": pos.get(d.id), "path": d.rel}
        for d in ls
    ] + [
        {"id": c.id, "type": "concept", "title": c.meta["title"], "stage": c.meta.get("stage"),
         "path": c.rel, "status": c.meta.get("status", "published")}
        for c in concepts()
    ]
    edges = (
        [{"from": d.id, "to": r, "kind": "requires_lesson"}
         for d in ls for r in d.meta.get("lessons_required", []) or []]
        + [{"from": d.id, "to": c, "kind": "teaches"}
           for d in ls for c in d.meta.get("concepts_taught", []) or []]
        + [{"from": d.id, "to": c, "kind": "uses"}
           for d in ls for c in d.meta.get("concepts_required", []) or []]
        + [{"from": c.id, "to": o, "kind": "contrasts_with"}
           for c in concepts() for o in c.meta.get("contrasts_with", []) or []]
    )
    return {"nodes": nodes, "edges": edges, "taught": taught, "used": used,
            "unlocks": unlocks, "by_id": by_id, "order": order}


def link_to(frm, to) -> str:
    import os
    rel = os.path.relpath(to.path, frm.path.parent)
    return f"[{to.meta['title']}]({rel})"


def lesson_block(d, g) -> str:
    by_id, concept_pages = g["by_id"], {c.id: c for c in concepts()}
    header = (f"**Stage:** `{d.meta['stage']}` · **Level:** {d.meta['level']} · "
              f"**~{d.meta['estimated_minutes']} min**")
    out = [header, ""]
    req = [by_id[r] for r in d.meta.get("lessons_required", []) or [] if r in by_id]
    if req:
        out += ["**You need first:** " + " · ".join(link_to(d, r) for r in req), ""]
    uses = [concept_pages[c] for c in d.meta.get("concepts_required", []) or [] if c in concept_pages]
    if uses:
        out += ["**Concepts assumed:** " + " · ".join(link_to(d, c) for c in uses), ""]
    nxt = [by_id[u] for u in g["unlocks"].get(d.id, []) if u in by_id]
    if nxt:
        out += ["**This unlocks:** " + " · ".join(link_to(d, n) for n in nxt), ""]
    return "\n".join(out)


def concept_block(c, g) -> str:
    by_id, pages = g["by_id"], {x.id: x for x in concepts()}
    out = []
    t = [by_id[l] for l in g["taught"].get(c.id, []) if l in by_id]
    if t:
        out += ["**Taught in:** " + " · ".join(link_to(c, x) for x in t), ""]
    u = [by_id[l] for l in g["used"].get(c.id, []) if l in by_id]
    if u:
        out += ["**Used in:** " + " · ".join(link_to(c, x) for x in u), ""]
    k = [pages[o] for o in c.meta.get("contrasts_with", []) or [] if o in pages]
    if k:
        out += ["**Do not confuse with:** " + " · ".join(link_to(c, x) for x in k), ""]
    return "\n".join(out) or "_Not yet linked into the course._\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    g = build()
    stale: list[str] = []

    def apply(doc, render) -> None:
        text = doc.path.read_text()
        n = 0

        def sub(m):
            nonlocal n
            n += 1
            return m.group(1) + "\n" + render(doc, g) + m.group(3)

        new = BLOCK.sub(sub, text)
        if n and new != text:
            if args.check:
                stale.append(doc.rel)
            else:
                doc.path.write_text(new)

    for d in lessons():
        apply(d, lesson_block)
    for c in concepts():
        apply(c, concept_block)

    payload = json.dumps({"nodes": g["nodes"], "edges": g["edges"]}, indent=2) + "\n"
    if args.check:
        if GRAPH_JSON.exists() and GRAPH_JSON.read_text() != payload:
            stale.append(str(GRAPH_JSON.relative_to(ROOT)))
        if stale:
            print("stale generated blocks: " + ", ".join(stale), file=sys.stderr)
            print("run: uv run python tools/build_graph.py", file=sys.stderr)
            return 1
        return 0

    if g["nodes"]:
        GRAPH_JSON.write_text(payload)
    print(f"graph: {len(g['nodes'])} nodes, {len(g['edges'])} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
