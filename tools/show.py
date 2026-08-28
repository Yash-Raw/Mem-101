"""Print what a lesson's lab produces once it is solved.

The README's first instruction to a newcomer is to run a lab, and every
`lab.py` ships a stub that raises `NotImplementedError` on the first call.
That is the exercise working correctly and a terrible first five minutes --
a clean clone met a traceback before it met a single number.

So this runs any lesson's lab with the reference solution patched over the
stubs, which is exactly the output the lesson's "Expected output" section
quotes. It reuses `validate_expected_output.lab_output`, so what you see
here is what CI checks the prose against -- one code path, not two.

    uv run python tools/show.py memory-is-not-rag
    uv run python tools/show.py                     # list what you can run
"""

from __future__ import annotations

import sys

from _common import ROOT, syllabus_lessons
from validate_expected_output import lab_output


def runnable() -> dict[str, tuple]:
    """Lesson id -> (level, lab directory), for every lesson that ships a lab."""
    found = {}
    for level, _module, lesson in syllabus_lessons():
        lab = ROOT / "curriculum" / level / lesson["id"] / "lab"
        if (lab / "lab.py").exists():
            found[lesson["id"]] = (level, lab)
    return found


def main() -> int:
    labs = runnable()
    if len(sys.argv) != 2:
        print(f"{len(labs)} labs. Pass one of these lesson ids:\n")
        for lid, (level, _) in labs.items():
            print(f"  {level:12} {lid}")
        print("\n  uv run python tools/show.py memory-is-not-rag")
        return 0

    wanted = sys.argv[1].strip("/").split("/")[-1]
    if wanted not in labs:
        print(f"No lab called {wanted!r}.", file=sys.stderr)
        near = [k for k in labs if wanted in k or k in wanted]
        if near:
            print("Did you mean: " + ", ".join(near), file=sys.stderr)
        else:
            print("Run without arguments to list them all.", file=sys.stderr)
        return 1

    _level, lab = labs[wanted]
    print(lab_output(lab, wanted.replace("-", "_")), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
