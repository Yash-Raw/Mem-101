#!/usr/bin/env python3
"""Weld content to code: every capstone_piece must actually import."""
from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import ROOT, Problems, lessons

SRC = ROOT / "capstone" / "src"


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
        piece = d.meta.get("capstone_piece")
        if not piece:
            continue
        claimed.add(piece)
        mod, _, attr = piece.rpartition(".")
        try:
            m = importlib.import_module(piece)
            _ = m
        except ModuleNotFoundError:
            try:
                m = importlib.import_module(mod)
            except Exception as e:  # noqa: BLE001
                p.add(d.rel, f"capstone_piece '{piece}' does not import: {e}")
                continue
            if not hasattr(m, attr):
                p.add(d.rel, f"capstone_piece '{piece}' — '{mod}' has no '{attr}'")
        except Exception as e:  # noqa: BLE001
            p.add(d.rel, f"capstone_piece '{piece}' raised on import: {e}")

    # Orphan detection: a memlab module no lesson claims.
    pkg = SRC / "memlab"
    if pkg.exists():
        for m in pkgutil.walk_packages([str(pkg)], prefix="memlab."):
            name = m.name
            if name.rsplit(".", 1)[-1].startswith("_") or m.ispkg:
                continue
            if not any(c == name or c.startswith(name + ".") for c in claimed):
                rel = Path(name.replace(".", "/")).with_suffix(".py")
                print(f"  warn  capstone/src/{rel}: no lesson claims this module")

    return p.report("capstone")


if __name__ == "__main__":
    raise SystemExit(main())
