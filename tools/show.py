"""Print what a lesson's lab produces once it is solved -- or check your own.

The README's first instruction to a newcomer is to run a lab, and every
`lab.py` ships a stub that raises `NotImplementedError` on the first call.
That is the exercise working correctly and a terrible first five minutes --
a clean clone met a traceback before it met a single number.

So this runs any lesson's lab with the reference solution patched over the
stubs, which is exactly the output the lesson's "Expected output" section
quotes. It reuses `validate_expected_output.lab_output`, so what you see
here is what CI checks the prose against -- one code path, not two.

`--check` answers the other question, the one nothing else in this repo
answers: *did I get it right?* Every `test_lab.py` deliberately pins the
reference solution rather than your code, and the first test in each asserts
the stub still raises -- so solving a lab turns that test red, and pytest
never tells you that you succeeded. This does. It runs YOUR `lab.py` with
nothing patched over it and diffs the output against the reference. The fake
backend is deterministic, so a correct implementation matches byte for byte.

    uv run python tools/show.py memory-is-not-rag
    uv run python tools/show.py --check memory-is-not-rag
    uv run python tools/show.py                     # list what you can run
"""

from __future__ import annotations

import difflib
import sys

from _common import ROOT, syllabus_lessons
from validate_expected_output import lab_output, learner_output


def runnable() -> dict[str, tuple]:
    """Lesson id -> (level, lab directory), for every lesson that ships a lab."""
    found = {}
    for level, _module, lesson in syllabus_lessons():
        lab = ROOT / "curriculum" / level / lesson["id"] / "lab"
        if (lab / "lab.py").exists():
            found[lesson["id"]] = (level, lab)
    return found


def _paint(text: str, code: str) -> str:
    """Colour only when a human is watching; a pipe or a log gets plain text."""
    return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text


def check(lesson: str, lab, slug: str) -> int:
    """Diff the learner's own lab against the reference. 0 if they match."""
    try:
        mine = learner_output(lab, slug)
    except NotImplementedError as e:
        print(_paint("not attempted yet", "33") + f" -- {lesson}")
        print(f"\n  The stub is still raising: {e}")
        print("  Fill it in, then run this again. To see the target:"
              f"\n      uv run python tools/show.py {lesson}")
        return 1
    except Exception as e:  # noqa: BLE001
        print(_paint("it raised", "31") + f" -- {lesson}")
        print(f"\n  {type(e).__name__}: {e}")
        print("\n  That is a bug in your implementation, not a wrong answer."
              "\n  Fix the traceback first, then run this again.")
        return 1

    reference = lab_output(lab, slug)
    if mine == reference:
        print(_paint("correct", "32") + f" -- {lesson}")
        print("\n  Your lab prints exactly what the lesson quotes."
              "\n  (`pytest` will now fail `test_stub_is_runnable`. That is the"
              "\n   exercise working -- it asserts the stub is still undone.)")
        return 0

    print(_paint("not yet", "31") + f" -- {lesson}")
    print("\n  Your output differs from the reference. `-` is yours, `+` is expected:\n")
    diff = difflib.unified_diff(
        mine.splitlines(), reference.splitlines(),
        fromfile="your lab.py", tofile="reference", lineterm="", n=1,
    )
    shown = 0
    for line in diff:
        if line.startswith(("---", "+++")):
            continue
        print("    " + line)
        shown += 1
        if shown >= 40:
            print("    ... (truncated)")
            break
    print("\n  The fake backend is deterministic, so this is a real difference,"
          "\n  not rounding. When comparing beats grinding, read solution.py.")
    return 1


def main() -> int:
    labs = runnable()
    args = [a for a in sys.argv[1:] if a != "--check"]
    wants_check = "--check" in sys.argv[1:]

    if len(args) != 1:
        print(f"{len(labs)} labs. Pass one of these lesson ids:\n")
        for lid, (level, _) in labs.items():
            print(f"  {level:12} {lid}")
        print("\n  uv run python tools/show.py memory-is-not-rag"
              "\n  uv run python tools/show.py --check memory-is-not-rag")
        return 0

    wanted = args[0].strip("/").split("/")[-1]
    if wanted not in labs:
        print(f"No lab called {wanted!r}.", file=sys.stderr)
        near = [k for k in labs if wanted in k or k in wanted]
        if near:
            print("Did you mean: " + ", ".join(near), file=sys.stderr)
        else:
            print("Run without arguments to list them all.", file=sys.stderr)
        return 1

    _level, lab = labs[wanted]
    slug = wanted.replace("-", "_")
    if wants_check:
        return check(wanted, lab, slug)
    print(lab_output(lab, slug), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
