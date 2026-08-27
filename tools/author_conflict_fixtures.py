#!/usr/bin/env python3
"""Hand-author the conflict classifier's fixtures. No model is called.

Every pair below is one the SLOT grouping surfaces -- same subject, same
attribute -- labelled with what the relationship actually is. Keyed on the pair
of contents alone, so editing an extraction fixture never invalidates these.

The labels are the interesting part. Note how many same-slot pairs are
`compatible`: filling the same attribute is what makes two claims worth
COMPARING, not evidence that they disagree.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "capstone" / "src"))

from memlab.evolve.conflict import SCHEMA, Relation, build_messages
from memlab.llm.fake import register_fixture

C, R, D, K = (
    Relation.CONTRADICTION.value,
    Relation.REFINEMENT.value,
    Relation.DUPLICATE.value,
    Relation.COMPATIBLE.value,
)

PAIRS: list[tuple[str, str, str]] = [
    # --- employer: the case similarity scored at 0.285, below noise ---
    ("Priya is a data engineer at Northwind Labs", "Priya works at Calico Systems", C),
    ("Priya is a data engineer at Northwind Labs", "Priya is a staff engineer", C),
    ("Priya works at Calico Systems", "Priya is a staff engineer", K),

    # --- diet: one refinement, one addition, and six that simply coexist ---
    ("Priya is vegetarian", "Priya eats fish", C),
    ("Priya is vegetarian", "Priya does not eat meat", K),
    ("Priya is vegetarian", "Priya is pescatarian", R),
    ("Priya is vegetarian", "Priya has a gluten intolerance", K),
    ("Priya eats fish", "Priya does not eat meat", K),
    ("Priya eats fish", "Priya is pescatarian", K),
    ("Priya eats fish", "Priya has a gluten intolerance", K),
    ("Priya does not eat meat", "Priya is pescatarian", K),
    ("Priya does not eat meat", "Priya has a gluten intolerance", K),
    ("Priya is pescatarian", "Priya has a gluten intolerance", K),

    # --- beverage: not drinking coffee and drinking tea are compatible ---
    ("Priya does not drink coffee", "Priya drinks tea", K),
    ("Priya does not drink coffee", "Priya drinks three coffees a day", C),
    ("Priya drinks tea", "Priya drinks three coffees a day", K),

    # --- response style ---
    ("Priya prefers detailed explanations with reasoning", "Priya prefers shorter answers", C),

    # --- the partner: a promotion refines the earlier role ---
    ("Priya's partner Sam is a nurse at St. Aubyn's", "She works nights most of the month", K),
    ("Priya's partner Sam is a nurse at St. Aubyn's", "Samira is a charge nurse", R),
    ("Priya's partner Sam is a nurse at St. Aubyn's", "Sam still works nights", K),
    ("She works nights most of the month", "Samira is a charge nurse", K),
    ("She works nights most of the month", "Sam still works nights", D),
    ("Samira is a charge nurse", "Sam still works nights", K),

    # --- residence: hearsay against a first-party fact ---
    ("Priya lives at 47 Halloway Road, Bristol",
     "Priya's colleague mentioned she is relocating to Berlin.", C),
]


def main() -> int:
    for a, b, relation in PAIRS:
        register_fixture(build_messages(a, b), {"relation": relation}, SCHEMA)

    counts = {}
    for *_, relation in PAIRS:
        counts[relation] = counts.get(relation, 0) + 1
    print(f"authored {len(PAIRS)} conflict fixtures")
    for relation, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {relation:<15} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
