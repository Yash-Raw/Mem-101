"""memlab -- the memory layer you build across this course.

Importing this package installs exactly one thing: a hook that appends a short
"what to do next" note when a **lab stub** raises `NotImplementedError`.

That traceback is the first thing a newcomer sees. Every `lab.py` ships one
unimplemented function, so meeting it is the exercise working correctly -- but
it used to end at a bare `NotImplementedError: implement retrieve_topk` with no
indication that this was expected or what to do about it. `tools/show.py` was
written to soften that landing, and it only helps someone who already knows it
exists. The message a learner actually reads should say so itself.

The hook is deliberately narrow, and it never replaces behaviour:

  * it chains to whatever hook was already installed, first, always;
  * it fires only for `NotImplementedError`;
  * it fires only when the deepest frame is a `curriculum/<level>/<lesson>/lab/lab.py`.

Any other use of this package -- a real traceback, a different exception, code
outside a lab -- is untouched.
"""

from __future__ import annotations

import pathlib
import sys

_previous_hook = sys.excepthook


def _lesson_of(tb) -> str | None:
    """The lesson id, if the exception surfaced inside a lab stub."""
    frame = tb
    while frame.tb_next is not None:
        frame = frame.tb_next
    path = pathlib.Path(frame.tb_frame.f_code.co_filename)
    if path.name != "lab.py" or path.parent.name != "lab":
        return None
    return path.parent.parent.name


def _hook(kind, value, tb) -> None:
    _previous_hook(kind, value, tb)
    if not issubclass(kind, NotImplementedError):
        return
    lesson = _lesson_of(tb)
    if lesson is None:
        return
    print(
        f"\nThat is the exercise, not a bug. This lab ships one stubbed function,"
        f"\nand the TODO just above it says what it must return.\n"
        f"\n  check your answer   uv run python tools/show.py --check {lesson}"
        f"\n  see the target      uv run python tools/show.py {lesson}\n",
        file=sys.stderr,
    )


if not getattr(sys.excepthook, "_memlab", False):
    _hook._memlab = True
    sys.excepthook = _hook
