"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Release:
    version: str
    lessons: int
    tests: int
    exams: dict[str, str]
    cost: dict[str, str]
    open_items: tuple[tuple[str, str], ...]

    @property
    def complete(self) -> bool:
        """A release is not "done"; it is shipped with its gaps written down."""
        return bool(self.open_items)


def report(lessons: int, tests: int) -> Release:
    return Release(
        version="0.3",
        lessons=lessons,
        tests=tests,
        exams={
            "belief": "passes from @I4",
            "context (k=5)": "passes from @I6",
            "budgeted": "51 tokens from @I8; derived floor 43",
        },
        cost={
            "write path": "2.0 model calls and 1.6 embeddings per turn",
            "read path": "no model calls; 2 embeddings warm",
            "blocking": "81% of per-turn cost, all of it extraction",
        },
        open_items=(
            ("extraction", "1 conditional clause stated in 24 turns, and it is "
                           "dropped: the reason a step matters is lost — "
                           "learning-from-outcomes"),
            ("vocabulary", "9 of 37 memories claim no modelled slot, so nothing "
                           "can contradict them — provenance-and-trust"),
            ("extraction leakage", "a deleted record's timestamp survives in 4 "
                                   "other records with 0 edges to follow — "
                                   "memory-attacks"),
            ("observability", "what was in the context is unrecorded; access_count "
                              "is 0 of 37 — memory-observability"),
            ("consolidation cost", "candidate pairs grow 104x for 8x the store — "
                                   "scaling-the-store"),
            ("evaluation", "1 of 4 component metrics distinguishes any two "
                           "profiles — reading-benchmark-claims"),
        ),
    )


def unfinished(release: Release) -> int:
    return len(release.open_items)


def lines(release: Release) -> list[str]:
    out = [f"memlab v{release.version} — {release.lessons} lessons, "
           f"{release.tests} tests", "", "  exams"]
    out += [f"    {k:16}{v}" for k, v in release.exams.items()]
    out += ["", "  cost"]
    out += [f"    {k:16}{v}" for k, v in release.cost.items()]
    out += ["", f"  open ({unfinished(release)})"]
    out += [f"    {k:20}{v}" for k, v in release.open_items]
    return out
