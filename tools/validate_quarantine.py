#!/usr/bin/env python3
"""Keep tools, vendors, and benchmark numbers out of the conceptual spine.

Rationale lives in landscape/index.md: during research for this course the same
system was found cited at two wildly different scores on the same benchmark,
from a third-party comparison and a vendor blog. Numbers like that have a shelf
life of weeks. They belong in dated, banner-flagged quarantine pages.
"""
from __future__ import annotations

import re
import sys

import yaml

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import LANDSCAPE, Problems, concepts, lessons

BLOCK = re.compile(r"<!--\s*landscape:begin\s*-->.*?<!--\s*landscape:end\s*-->", re.DOTALL)
FENCE = re.compile(r"```.*?```", re.DOTALL)
NUMBER = re.compile(r"\b\d{1,3}\.\d\s*%|\b\d{1,3}\s*%")


def main() -> int:
    p = Problems()
    reg = yaml.safe_load((LANDSCAPE / "registry.yml").read_text())
    names = sorted({n for group in reg.values() for n in group}, key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(re.escape(n) for n in names) + r")\b")

    for d in lessons() + concepts():
        # Strip the sanctioned block and code fences, then look for leaks.
        clean = FENCE.sub("", BLOCK.sub("", d.body))
        for m in pattern.finditer(clean):
            line = clean[: m.start()].count("\n") + 1
            p.add(d.rel, f"line ~{line}: '{m.group(1)}' must sit inside a landscape:begin/end block")
        # Benchmark-shaped numbers near a registry name are the other leak.
        for m in NUMBER.finditer(clean):
            window = clean[max(0, m.start() - 120) : m.end() + 120]
            if pattern.search(window):
                p.add(d.rel, f"benchmark number '{m.group(0).strip()}' outside landscape/")

    return p.report("quarantine")


if __name__ == "__main__":
    raise SystemExit(main())
