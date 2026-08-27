#!/usr/bin/env python3
"""syllabus.yml and the filesystem must agree, and every lab must be complete."""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import CURRICULUM, Problems, lessons, syllabus_lessons


def main() -> int:
    p = Problems()
    planned = {l["id"]: (lv, m) for lv, m, l in syllabus_lessons()}
    on_disk = {d.id: d for d in lessons()}

    for lid, d in on_disk.items():
        if lid not in planned:
            p.add(d.rel, "lesson exists on disk but is not in syllabus.yml")
        else:
            level, _ = planned[lid]
            expect = CURRICULUM / level / lid / "index.md"
            if d.path != expect:
                p.add(d.rel, f"should live at {expect.relative_to(CURRICULUM.parent)}")

    # Labs: a lesson that declares one must ship stub + solution + test.
    for lid, d in on_disk.items():
        lab = d.meta.get("lab")
        if not lab:
            continue
        base = d.path.parent / lab
        for f in (base, base.parent / "solution.py", base.parent / "test_lab.py"):
            if not f.exists():
                p.add(d.rel, f"declares a lab but {f.name} is missing")

    for labdir in CURRICULUM.glob("*/*/lab"):
        idx = labdir.parent / "index.md"
        if not idx.exists():
            p.add(str(labdir), "orphan lab directory with no lesson")

    # Every lab has a module named `solution`; a bare import resolves to
    # whichever one landed in sys.modules first. Tests must use memlab.labkit.
    for test in CURRICULUM.glob("*/*/lab/test_lab.py"):
        src = test.read_text()
        rel = str(test.relative_to(CURRICULUM.parent))
        for bad in ("from solution import", "import solution", "\n    import lab\n"):
            if bad in src:
                p.add(rel, f"{bad.strip()!r} collides across labs; use memlab.labkit")
        if "sys.path.insert" in src:
            p.add(rel, "sys.path manipulation in a test; use memlab.labkit")

    return p.report("structure")


if __name__ == "__main__":
    raise SystemExit(main())
