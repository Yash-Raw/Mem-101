"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Failure:
    """One symptom, its causes, and the measurement that separates them."""

    symptom: str
    causes: tuple[str, ...]
    distinguish: str
    met_in: str

    @property
    def ambiguous(self) -> bool:
        return len(self.causes) > 1


def field_guide() -> list[Failure]:
    return [
        Failure(
            "the assistant argues with a correction",
            ("consolidation deferred past the contested turn",
             "arbitration lost to a newer agent write"),
            "replay turn by turn and diff against an eager store",
            "sleep-time-compute, cross-agent-write-conflicts",
        ),
        Failure(
            "a fact the user gave is never recalled",
            ("never extracted",
             "extracted but unnameable, so never arbitrated",
             "demoted out of the retrievable tier"),
            "check the store, then slot_of, then the eligible pool",
            "provenance-and-trust, temporal-questions",
        ),
        Failure(
            "the answer is right and the context is wrong",
            ("packer dropped a required fact under budget",
             "a composite displaced its own sources"),
            "compare the belief exam with the context exam",
            "slot-value, reflection-and-insight",
        ),
        Failure(
            "deleted data reappears",
            ("cascade missed a structure",
             "a derived record still carries the value"),
            "re-scan every structure by id after deleting",
            "deletion-that-actually-deletes",
        ),
        Failure(
            "half the store stops being retrievable",
            ("one future-dated write re-aged everything",),
            "compare the eligible pool before and after a write",
            "memory-access-control",
        ),
        Failure(
            "writes disappear during a batch",
            ("read-modify-write with no snapshot",),
            "add a memory mid-job and count it afterwards",
            "background-job-mechanics",
        ),
        Failure(
            "a metric improves and nothing got better",
            ("the metric was already saturated",
             "the harness shared state between versions"),
            "check whether the metric moved at that change",
            "end-to-end-eval, reading-benchmark-claims",
        ),
    ]


def ambiguous(failures: list[Failure]) -> list[Failure]:
    """Symptoms with more than one cause -- where a guide earns its keep."""
    return [f for f in failures if f.ambiguous]


def coverage(failures: list[Failure]) -> tuple[int, int]:
    """(failures with a lesson that measured them, total)."""
    return sum(1 for f in failures if f.met_in), len(failures)
