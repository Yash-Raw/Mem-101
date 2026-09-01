#!/usr/bin/env python3
"""Every relative link and #anchor must resolve on disk (convention C5).

Two blind spots this used to have, both found by writing a dead link and
watching the validator pass:

* **HTML links were never read.** Only `[text](href)` was matched. Raw HTML in
  a markdown page cannot use a `.md` target -- mkdocs rewrites markdown links
  but not anchors inside an HTML block, so those hrefs are site-relative by
  necessity and C5 cannot apply. What they *must not* contain is an unevaluated
  `{{ ... }}`: mkdocs does not expand Jinja in page content. `timeline.md`
  shipped `href="{{ base_url }}/..."` to production and all 21 links 404'd,
  which is the check this now performs.
* **Root pages were never scanned.** `lessons() + concepts() + landscape()`
  skips README.md, MEMLAB.md, map.md, atlas.md and timeline.md, because
  `parse()` returns None for a file with no frontmatter. MEMLAB.md is linked
  *from* lesson 1, so it is very much part of the site.

Root pages get a slightly different rule: C5's "must end in .md" is about
cross-links between pages, and the README legitimately links to LICENSE. There,
a non-.md target is allowed if it actually exists on disk.
"""
from __future__ import annotations

import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import ROOT, Doc, Problems, concepts, landscape, lessons, syllabus_lessons

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
HTML_LINK = re.compile(r'<a\s[^>]*?href="([^"]+)"')

# Site pages with no frontmatter, so `parse()` skips them.
STANDALONE = ("README.md", "MEMLAB.md", "SYLLABUS.md", "CONTRIBUTING.md",
              "map.md", "atlas.md", "timeline.md")


def standalone() -> list[Doc]:
    return [Doc(path=ROOT / n, meta={}, body=(ROOT / n).read_text())
            for n in STANDALONE if (ROOT / n).exists()]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9\- ]", "", text.lower()).replace(" ", "-")


def main() -> int:
    p = Problems()
    docs = lessons() + concepts() + landscape()
    loose = {d.rel for d in standalone()}   # root pages: see the module docstring
    docs += standalone()
    planned = {l['id'] for _, _, l in syllabus_lessons()}
    pending: set[str] = set()

    for d in docs:
        for href in HTML_LINK.findall(d.body):
            if "{{" in href or "{%" in href:
                p.add(d.rel, f"unevaluated template in href '{href}' — mkdocs does not "
                             "expand Jinja in page content, it ships the literal string")

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
                if d.rel in loose and (d.path.parent / target).exists():
                    continue      # README -> LICENSE and friends
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
