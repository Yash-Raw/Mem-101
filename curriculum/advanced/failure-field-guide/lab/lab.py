"""Lab: seven symptoms, and the measurement that tells them apart.

    uv run python curriculum/advanced/failure-field-guide/lab/lab.py
"""

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
    raise NotImplementedError("implement field_guide")


def ambiguous(failures: list[Failure]) -> list[Failure]:
    """Symptoms with more than one cause -- where a guide earns its keep."""
    raise NotImplementedError("implement ambiguous")


def coverage(failures: list[Failure]) -> tuple[int, int]:
    """(failures with a lesson that measured them, total)."""
    raise NotImplementedError("implement coverage")


def main() -> None:
    failures = field_guide()
    for failure in failures:
        print(f"   {failure.symptom}")
        print(f"      causes ({len(failure.causes)}): "
              f"{' | '.join(failure.causes)}")
        print(f"      tell   : {failure.distinguish}")
        print(f"      met in : {failure.met_in}")

    measured, total = coverage(failures)
    print(f"\n   failures with more than one cause: "
          f"{len(ambiguous(failures))} of {total}")
    print(f"   measured somewhere in the course : {measured} of {total}")


if __name__ == "__main__":
    main()
