"""Import helpers for lab tests.

Every lab ships `lab.py` and `solution.py`. Eighty-four labs means eighty-four
modules named `solution`, and a plain `import solution` resolves to whichever
one landed in `sys.modules` first -- so the second lab collected in a run gets
the first lab's code. Silent, and it produces baffling failures.

So labs never import by bare name. `load(__file__, "solution")` loads the file
sitting next to the caller under a path-derived unique module name.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load(test_file: str | Path, name: str) -> ModuleType:
    """Load `name`.py from the directory containing `test_file`."""
    here = Path(test_file).resolve().parent
    path = here / f"{name}.py"
    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")

    # Unique per lab: curriculum/beginner/<lesson>/lab/solution.py -> lab_<lesson>_solution
    unique = f"lab_{here.parent.name.replace('-', '_')}_{name}"
    if unique in sys.modules:
        return sys.modules[unique]

    spec = importlib.util.spec_from_file_location(unique, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique] = module
    spec.loader.exec_module(module)
    return module


def solution(test_file: str | Path) -> ModuleType:
    return load(test_file, "solution")


def lab(test_file: str | Path) -> ModuleType:
    return load(test_file, "lab")
