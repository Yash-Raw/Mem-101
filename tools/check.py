#!/usr/bin/env python3
"""Run the whole validator suite. This is what CI runs."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
SUITE = [
    "validate_frontmatter.py",
    "validate_structure.py",
    "validate_graph.py",
    "validate_links.py",
    "validate_quarantine.py",
    "validate_capstone.py",
    "validate_expected_output.py",
    "validate_freshness.py",
]
GENERATED = [
    ("render_syllabus.py", "--check"),
    ("build_graph.py", "--check"),
    ("render_nav.py", "--check"),
    # Last: it reads concepts/graph.json, which build_graph.py has just checked.
    ("build_site_data.py", "--check"),
]


def main() -> int:
    print("validators")
    rc = 0
    for script in SUITE:
        if (TOOLS / script).exists():
            rc |= subprocess.run([sys.executable, str(TOOLS / script)], check=False).returncode
    print("generated files")
    for script, flag in GENERATED:
        if (TOOLS / script).exists():
            r = subprocess.run([sys.executable, str(TOOLS / script), flag],
                               capture_output=True, text=True, check=False)
            print(f"  {'ok  ' if r.returncode == 0 else 'FAIL'} {script}")
            if r.returncode:
                print("        " + (r.stderr or r.stdout).strip())
            rc |= r.returncode
    print("\n" + ("all checks passed" if rc == 0 else "CHECKS FAILED"))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
