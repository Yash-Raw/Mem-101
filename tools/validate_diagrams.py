#!/usr/bin/env python3
"""Convention C6, finally enforced -- plus the hole it left open.

CONTRIBUTING.md says the conventions "are enforced by validators, not by
review". C6 -- "Diagrams are fenced ```mermaid blocks, not image files" -- was
the exception: nothing checked it, nothing checked where a diagram sat, and
nothing checked what one said.

That last gap is the dangerous one. `validate_expected_output.py` verifies every
figure a lesson quotes against what its lab actually printed, but it strips
fenced blocks first (`FENCE = re.compile(r"```.*?```")`) because fences are full
of traces and timestamps. A mermaid diagram is a fence. So a number written
inside a diagram is invisible to the check that exists precisely because seven
figures across five lessons went stale.

Two diagrams already carry `36`. Both are fine -- 36 appears in the prose of
both lessons, where the expected-output check can see it. That is the rule this
validator makes permanent: a diagram may repeat a measured number, but never be
the only place it appears.

    uv run python tools/validate_diagrams.py
"""
from __future__ import annotations

import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import Problems, lessons

MERMAID = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
ANY_FENCE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
HEADING = re.compile(r"^## (.+)$", re.MULTILINE)

# The section every one of the 22 existing diagrams sits under, without
# exception. A diagram elsewhere is either misplaced or a new convention that
# should be argued for rather than slipped in.
HOME = "Mechanism"

# What means "this is a diagram", so a fence tagged anything else (or nothing)
# is a C6 violation rather than a code sample. Deliberately conservative: the
# first draft matched a bare `graph ` and flagged a lab trace that opens
# "graph shape: {...}". Mermaid always follows `graph`/`flowchart` with a
# direction, and the camelCase keywords stand alone -- the loose words `pie`,
# `gantt`, `journey` and `timeline` are left out, because a missed diagram is a
# cheaper mistake than a validator that cries wolf about output.
DIAGRAM_START = re.compile(
    r"^(?:(?:flowchart|graph)\s+(?:TB|TD|BT|RL|LR)\b"
    r"|(?:sequenceDiagram|classDiagram|stateDiagram(?:-v2)?|erDiagram"
    r"|quadrantChart|xychart-beta|mindmap)\s*$)",
    re.MULTILINE,
)

# The house palette, applied by hand across all 22 and never varied:
# blue = the mechanism this lesson teaches, yellow = the gate or judgement
# call, red = the failure. A fourth colour would be a fourth meaning.
PALETTE = {
    ("#aed6f1", "#2874a6"),   # mechanism
    ("#f9e79f", "#b7950b"),   # gate / decision
    ("#f5b7b1", "#c0392b"),   # failure / anti-pattern
}
FILL_STROKE = re.compile(r"fill:\s*(#[0-9a-fA-F]{3,6})\s*,\s*stroke:\s*(#[0-9a-fA-F]{3,6})")

# Same shape as validate_expected_output.FIGURE: 2+ digit integers and 3dp
# decimals are measurements; a lone digit or a year is prose.
FIGURE = re.compile(r"(?<![\w.,:#\-])(\d{2,4}|\d\.\d{3})(?![\w.,:%])")
STYLING = ("style ", "classDef ", "linkStyle ", "class ")


def _sections(body: str) -> list[tuple[str, int, int]]:
    """(title, start, end) for each `## ` section, in document order."""
    marks = [(m.group(1).strip(), m.start()) for m in HEADING.finditer(body)]
    out = []
    for i, (title, start) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(body)
        out.append((title, start, end))
    return out


def _prose(body: str) -> str:
    """The lesson with every fence removed -- what the figure checks can see."""
    return ANY_FENCE.sub(" ", body)


def main() -> int:
    p = Problems()
    drawn = 0

    for d in lessons():
        body = d.path.read_text()
        prose = _prose(body)
        sections = _sections(body)

        # C6: a diagram must be tagged `mermaid`, or Material ships it as a
        # code block and GitHub renders it as text.
        for tag, inner in ANY_FENCE.findall(body):
            head = inner.lstrip()
            if tag != "mermaid" and DIAGRAM_START.match(head):
                p.add(d.rel, f"C6: diagram in a ```{tag or 'untagged'} fence; use ```mermaid")

        for m in MERMAID.finditer(body):
            drawn += 1
            inner = m.group(1)
            where = next(
                (t for t, s, e in sections if s <= m.start() < e), "(no section)"
            )
            if where != HOME:
                p.add(d.rel, f"diagram under '## {where}'; all diagrams live under '## {HOME}'")

            for fill, stroke in FILL_STROKE.findall(inner):
                if (fill.lower(), stroke.lower()) not in PALETTE:
                    p.add(d.rel, f"off-palette {fill}/{stroke}; see tools/validate_diagrams.py")

            # A figure inside a fence is invisible to validate_expected_output.
            # It may appear here, but it may not appear ONLY here.
            claims = "\n".join(
                ln for ln in inner.splitlines()
                if not ln.strip().startswith(STYLING)
            )
            for fig in sorted(set(FIGURE.findall(claims))):
                if fig not in prose:
                    p.add(
                        d.rel,
                        f"figure {fig!r} appears only inside a diagram, where no "
                        f"check can see it -- state it in the prose too",
                    )

    print(f"        ({drawn} diagrams across {len(lessons())} lessons)")
    return p.report("diagrams")


if __name__ == "__main__":
    raise SystemExit(main())
