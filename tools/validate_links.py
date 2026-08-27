#!/usr/bin/env python3
"""Every relative markdown link and #anchor must resolve on disk (convention C5)."""
from __future__ import annotations

import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import ROOT, Problems, concepts, landscape, lessons, syllabus_lessons

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9\- ]", "", text.lower()).replace(" ", "-")


def main() -> int:
    p = Problems()
    docs = lessons() + concepts() + landscape()
    planned = {l['id'] for _, _, l in syllabus_lessons()}
    pending: set[str] = set()

    for d in docs:
        for href in LINK.findall(d.body):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            if href.startswith("/"):
                p.add(d.rel, f"absolute link '{href}' — use a relative path (C5)")
                continue
            target, _, anchor = href.partition("#")
            if not target:
                if anchor and anchor not in {slug(h) for h in re.findall(r"^#+ (.+)$", d.body, re.MULTILINE)}:
                    p.add(d.rel, f"anchor '#{anchor}' not found in this page")
                continue
            if not target.endswith(".md"):
                p.add(d.rel, f"link '{href}' must end in .md so it renders on GitHub and the site (C5)")
                continue
            resolved = (d.path.parent / target).resolve()
            if not resolved.exists():
                # A link to a lesson that is planned but not yet authored is a
                # forward reference, not rot. Authoring is incremental; the
                # syllabus is the contract that the target will exist.
                if resolved.name == "index.md" and resolved.parent.name in planned:
                    pending.add(resolved.parent.name)
                    continue
                p.add(d.rel, f"dead link '{href}'")
            elif anchor:
                heads = {slug(h) for h in re.findall(r"^#+ (.+)$", resolved.read_text(), re.MULTILINE)}
                if anchor not in heads:
                    p.add(d.rel, f"dead anchor '{href}'")
    _ = ROOT
    if pending:
        print(f"  note  {len(pending)} forward link(s) to lessons not yet authored")
    return p.report("links")


if __name__ == "__main__":
    raise SystemExit(main())
