#!/usr/bin/env python3
"""Run the whole validator suite. This is what CI runs.

A name in SUITE or GENERATED that has no file is a FAILURE, not a skip. Both
loops used to be guarded by `.exists()`, so renaming or deleting a validator
removed it from the suite and CI stayed green -- the one hole in a repository
whose entire character is checking. The suite has to notice its own absence.
"""
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
    "validate_diagrams.py",
]
GENERATED = [
    ("render_syllabus.py", "--check"),
    ("build_graph.py", "--check"),
    ("render_nav.py", "--check"),
    # Last: it reads concepts/graph.json, which build_graph.py has just checked.
    ("build_site_data.py", "--check"),
]


def main() -> int:
    rc = 0
    print("validators", flush=True)
    for script in SUITE:
        if not (TOOLS / script).exists():
            print(f"  FAIL  {script} — listed in SUITE but the file is missing", flush=True)
            rc |= 1
            continue
        rc |= subprocess.run([sys.executable, str(TOOLS / script)], check=False).returncode
    print("generated files", flush=True)
    for script, flag in GENERATED:
        if not (TOOLS / script).exists():
            print(f"  FAIL  {script} — listed in GENERATED but the file is missing")
            rc |= 1
            continue
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
