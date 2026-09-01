#!/usr/bin/env python3
"""Weld content to code: every capstone_piece must actually import.

The same rule is applied to `MEMLAB.md`, the API reference a learner is sent to
from lesson 1. A reference page that drifts is worse than no reference page --
it sends someone confidently to a module that moved -- so every `from memlab
... import ...` line on it is executed here.

`capstone_piece` may be a single dotted path or a list of them -- a lesson that
builds two modules should say so rather than leaving one orphaned.

INFRASTRUCTURE names modules the course uses but never teaches: the fake LLM,
the lab loader, the pipeline registry, the exam reader. They are scaffolding for
the curriculum rather than subjects of it, and listing them here is a deliberate
statement to that effect -- an unexplained warning is one people learn to ignore.
"""

from __future__ import annotations

import importlib
import pkgutil
import re
import sys
from pathlib import Path

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import ROOT, Problems, lessons

SRC = ROOT / "capstone" / "src"
API_PAGE = ROOT / "MEMLAB.md"

# Deliberately taught by no lesson. Scaffolding, not subject matter.
INFRASTRUCTURE = frozenset({
    "memlab.labkit",          # loads each lab's modules without cross-import
    "memlab.pipeline",        # level profiles and module snapshots
    "memlab.fixtures",        # access to the canonical corpus
    "memlab.eval.exam",       # the headline metric's reader
    "memlab.llm.base",        # provider shim
    "memlab.llm.fake",        # the deterministic backend
    "memlab.llm.anthropic",   # the optional live backend
})


def main() -> int:
    p = Problems()
    ls = lessons()
    if not ls:
        print("  ok  capstone (no lessons authored yet)")
        return 0
    if not SRC.exists():
        print("  ok  capstone (package not scaffolded yet)")
        return 0

    sys.path.insert(0, str(SRC))
    claimed: set[str] = set()

    for d in ls:
        declared = d.meta.get("capstone_piece")
        if not declared:
            continue
        pieces = declared if isinstance(declared, list) else [declared]
        for piece in pieces:
            claimed.add(piece)
            _check_one(p, d, piece)

    _check_api_page(p)
    _warn_orphans(claimed)
    return p.report("capstone")


def _check_one(p, d, piece: str) -> None:
    """A declared capstone_piece must resolve to a module or an attribute."""
    mod, _, attr = piece.rpartition(".")
    try:
        importlib.import_module(piece)
        return
    except ModuleNotFoundError:
        pass
    except Exception as e:  # noqa: BLE001
        p.add(d.rel, f"capstone_piece '{piece}' raised on import: {e}")
        return

    try:
        m = importlib.import_module(mod)
    except Exception as e:  # noqa: BLE001
        p.add(d.rel, f"capstone_piece '{piece}' does not import: {e}")
        return

    if not hasattr(m, attr):
        p.add(d.rel, f"capstone_piece '{piece}' — '{mod}' has no '{attr}'")

IMPORT_LINE = re.compile(r"^from (memlab[\w.]*) import (.+)$")


def _check_api_page(p) -> None:
    """Every `from memlab ... import ...` line in MEMLAB.md must resolve."""
    if not API_PAGE.exists():
        return
    checked = 0
    for n, raw in enumerate(API_PAGE.read_text().splitlines(), 1):
        m = IMPORT_LINE.match(raw.strip())
        if not m:
            continue
        mod, names = m.group(1), m.group(2)
        try:
            module = importlib.import_module(mod)
        except Exception as e:  # noqa: BLE001
            p.add("MEMLAB.md", f"line {n}: '{mod}' does not import: {e}")
            continue
        for name in (x.strip() for x in names.split(",")):
            checked += 1
            if name and not hasattr(module, name):
                p.add("MEMLAB.md", f"line {n}: '{mod}' has no '{name}'")
    print(f"        (checked {checked} names on MEMLAB.md)")


def _warn_orphans(claimed: set[str]) -> None:
    """A memlab module no lesson claims and INFRASTRUCTURE does not excuse."""
    pkg = SRC / "memlab"
    if not pkg.exists():
        return
    for m in pkgutil.walk_packages([str(pkg)], prefix="memlab."):
        name = m.name
        if name.rsplit(".", 1)[-1].startswith("_") or m.ispkg:
            continue
        if name in INFRASTRUCTURE:
            continue
        if not any(c == name or c.startswith(name + ".") for c in claimed):
            rel = Path(name.replace(".", "/")).with_suffix(".py")
            print(f"  warn  capstone/src/{rel}: no lesson claims this module")


if __name__ == "__main__":
    raise SystemExit(main())
