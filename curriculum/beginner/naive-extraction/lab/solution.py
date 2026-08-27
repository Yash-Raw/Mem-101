"""Reference solution."""
from __future__ import annotations

from memlab.extract.naive import extract  # noqa: F401  (re-exported for the lab)
from memlab.types import Memory, MemoryType

PII_MARKERS = ("Halloway Road", "07700", "gluten intolerance")


def audit_against_gold(memories: list[Memory], gold: dict) -> dict[str, list[str]]:
    """Score the naive extractor against ground truth.

    Reports what it *failed to produce* as well as what it produced wrongly --
    the first category is the one that costs the headline question, and the one
    a store-shaped test can never see.
    """
    findings: dict[str, list[str]] = {}
    contents = [m.content for m in memories]

    # 1. The employer state that was never created.
    employer_states = [
        c for c in contents
        if "Calico" in c and any(v in c for v in ("works at", "is at"))
    ]
    if not any("works at Calico" in c for c in employer_states):
        events = [c for c in contents if "Calico" in c]
        findings["missing_state"] = [
            (
                f"no memory says 'Priya works at Calico Systems'; "
                f"the job change exists only as events: {events}"
            )
        ]

    # 2. PII that walked in with no gate.
    if pii := [c for c in contents if any(p in c for p in PII_MARKERS)]:
        findings["ungated_pii"] = pii

    # 3. A deletion request filed rather than honoured.
    target = gold["deletion_request"]["target"]
    filed = [c for c in contents if "forget" in c.lower()]
    still_there = [c for c in contents if "Halloway Road" in c]
    if filed and still_there:
        findings["unhonoured_deletion"] = [
            (
                f"request about {target!r} stored as {filed[0]!r}, "
                f"while {still_there[0]!r} remains"
            )
        ]

    return findings


def type_histogram(memories: list[Memory]) -> dict[str, int]:
    return {t.value: sum(1 for m in memories if m.type is t) for t in MemoryType}
