#!/usr/bin/env python3
"""Does each lesson's stated Expected output still match what its lab prints?

This validator exists because a grep-based staleness sweep passed while four
figures across three lessons were wrong. Those lessons were measured against
one pipeline snapshot, later re-pointed at a different one, and the prose was
never re-measured -- and the tests missed it because they had been written
tolerantly (`> 40` where the prose said 46).

Sampling is not verification. So this runs each lab for real: it loads
`solution.py` over `lab.py`'s stubs, calls `main()`, and checks that every
figure quoted in the lesson's **Expected output:** block actually appears in
what the lab printed.

A figure counts as verified if it appears in the lab's output OR is pinned in
the lesson's test file. That is the repo's own standard -- every number quoted
in a lesson is backed by something executable -- expressed as a check. Prose
figures that are neither ("17 months", "about forty lines") are excluded by
restricting the scan to the sections that claim to measure something.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import ROOT, Problems, parse, syllabus_lessons

# 2+ digit integers and 3dp decimals. Years are prose, not measurements.
FIGURE = re.compile(r"(?<![\w.,:])(\d{2,4}|\d\.\d{3})(?![\w.,:%])")
YEARS = frozenset({"2024", "2025", "2026", "2027"})

# Noise classes: figures here are never claims about the store.
FENCE = re.compile(r"```.*?```", re.DOTALL)          # traces and code, full of timestamps
INLINE = re.compile(r"`[^`]*`")                 # identifiers, thresholds in code voice
TABLE_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")  # lesson cross-links
SESSION = re.compile(r"[Ss]ession[- ]\d+")           # names a turn, not a measurement
QUOTED = re.compile(r"\*\"[^\"]*\"\*")                 # verbatim corpus text, not a claim


def _load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def lab_output(lab_dir: pathlib.Path, slug: str) -> str:
    """Run the lab as if the learner had solved it."""
    solution = _load(lab_dir / "solution.py", f"_eo_sol_{slug}")
    lab = _load(lab_dir / "lab.py", f"_eo_lab_{slug}")
    for attr in dir(solution):
        if not attr.startswith("_") and hasattr(lab, attr):
            setattr(lab, attr, getattr(solution, attr))

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        lab.main()
    return buffer.getvalue()


# Sections whose figures are claims about the system, not turns of phrase.
MEASURING = ("The problem", "Mechanism", "Lab")


def measured_prose(body: str) -> str:
    """The sections that assert numbers about the store, lab, or corpus.

    Code fences, inline code and links are stripped: a timestamp in a trace or
    a threshold written in code voice is not a claim someone can re-measure.
    """
    text = "\n".join(
        section for section in re.split(r"\n## ", body)
        if section.startswith(MEASURING)
    )
    for pattern in (FENCE, INLINE, TABLE_LINK, SESSION, QUOTED):
        text = pattern.sub(" ", text)
    return text


def main() -> int:
    p = Problems()
    ran = 0

    for level, _module, lesson in syllabus_lessons():
        index = ROOT / "curriculum" / level / lesson["id"] / "index.md"
        lab_dir = index.parent / "lab"
        if not index.exists() or not (lab_dir / "lab.py").exists():
            continue

        doc = parse(index)
        block = measured_prose(doc.body)
        if not block.strip():
            continue
        test_src = (lab_dir / "test_lab.py").read_text() if (lab_dir / "test_lab.py").exists() else ""

        try:
            printed = lab_output(lab_dir, lesson["id"].replace("-", "_"))
        except Exception as e:  # noqa: BLE001
            p.add(doc.rel, f"lab main() failed with the reference solution: {e}")
            continue
        ran += 1

        figures = {f for f in FIGURE.findall(block) if f not in YEARS}
        unverified = sorted(f for f in figures if f not in printed and f not in test_src)
        if unverified:
            p.add(
                doc.rel,
                f"quotes {unverified} — not printed by the lab and not pinned by a "
                "test; re-measure, re-quote, and pin",
            )

    print(f"        (ran {ran} labs)")
    return p.report("expected-output")


if __name__ == "__main__":
    raise SystemExit(main())
