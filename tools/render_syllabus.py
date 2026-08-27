#!/usr/bin/env python3
"""Render SYLLABUS.md from curriculum/syllabus.yml.

syllabus.yml is the single source of truth for linear order (convention C2).
Run with --check in CI to fail when the committed output is stale.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SYLLABUS = ROOT / "curriculum" / "syllabus.yml"
OUT = ROOT / "SYLLABUS.md"

STAGE_BLURB = {
    "orientation": "framing the problem",
    "extract": "turns into facts",
    "store": "where facts live",
    "retrieve": "getting them back",
    "evolve": "keeping them true",
    "assemble": "fitting the budget",
    "govern": "privacy, eval, ops",
}


def lesson_path(level: str, lesson_id: str) -> str:
    return f"curriculum/{level}/{lesson_id}/index.md"


def render(doc: dict) -> str:
    levels = doc["levels"]
    lessons = [
        (lv, m, l) for lv in levels for m in lv["modules"] for l in m["lessons"]
    ]

    out: list[str] = []
    w = out.append

    w(f"# {doc['title']}")
    w("")
    w(f"> {doc['tagline']}")
    w("")
    w(
        f"{len(lessons)} lessons across {sum(len(lv['modules']) for lv in levels)} "
        f"modules and {len(levels)} levels. Every lesson carries a lifecycle "
        "`stage`, a prerequisite list, a runnable lab, and a piece of the capstone."
    )
    w("")
    w("<!-- generated:begin --> <!-- Do not edit: `uv run python tools/render_syllabus.py` -->")
    w("")

    # Stage distribution — the thesis, made visible as the sort order.
    w("## Where the mass sits")
    w("")
    w(
        "A RAG tutorial spends ~85% of its length on `retrieve`. This course does "
        "not, and the table below is the argument:"
    )
    w("")
    w("| Stage | | Lessons | Share |")
    w("|---|---|--:|--:|")
    total = len(lessons)
    for stage in doc["stages"]:
        n = sum(1 for _, _, l in lessons if l["stage"] == stage)
        bar = "█" * round(n / total * 40)
        w(f"| `{stage}` | {STAGE_BLURB[stage]} | {n} | {bar} {n/total:.0%} |")
    w("")

    # Level overview
    w("## The three levels")
    w("")
    for lv in levels:
        n = sum(len(m["lessons"]) for m in lv["modules"])
        w(f"### {lv['title']} · *{lv['question']}*")
        w("")
        w(f"{' '.join(lv['outcome'].split())}")
        w("")
        w(f"{n} lessons · {len(lv['modules'])} modules")
        w("")

    # Full contents
    w("## Contents")
    w("")
    n = 0
    for lv in levels:
        w(f"### {lv['title']}")
        w("")
        for m in lv["modules"]:
            w(f"**{m['title']}**")
            w("")
            w("| # | Lesson | Stage | You will be able to |")
            w("|--:|---|---|---|")
            for l in m["lessons"]:
                n += 1
                link = f"[{l['title']}]({lesson_path(lv['id'], l['id'])})"
                w(f"| {n} | {link} | `{l['stage']}` | {l['objective']} |")
            w("")

    w("<!-- generated:end -->")
    w("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if output is stale")
    args = ap.parse_args()

    doc = yaml.safe_load(SYLLABUS.read_text())
    rendered = render(doc)

    if args.check:
        current = OUT.read_text() if OUT.exists() else ""
        if current != rendered:
            print(
                "SYLLABUS.md is stale. Run: uv run python tools/render_syllabus.py",
                file=sys.stderr,
            )
            return 1
        print("SYLLABUS.md up to date")
        return 0

    OUT.write_text(rendered)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
