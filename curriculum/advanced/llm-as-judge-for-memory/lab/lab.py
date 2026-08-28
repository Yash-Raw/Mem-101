"""Lab: where a model decides, and what protects the result.

    uv run python curriculum/advanced/llm-as-judge-for-memory/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    GENERATION = "generation"   # produce candidates; downstream stages filter
    JUDGEMENT = "judgement"     # decide a label that changes what is believed
    ARBITRATION = "arbitration"  # decide which belief survives -- never a model


@dataclass(frozen=True)
class Use:
    """One place a model is called, and what protects the result."""

    site: str
    role: Role
    bounded_output: bool     # a fixed label set, not free text
    checked_against_gold: bool
    reproducible: bool       # fixture-backed, so two runs agree

    @property
    def safe(self) -> bool:
        """All three, or none. Any one missing and the others stop helping."""
        return self.bounded_output and self.checked_against_gold and self.reproducible


def uses() -> list[Use]:
    raise NotImplementedError("implement uses")


def arbitration_is_never_a_model() -> str:
    """Stated as a rule because it is one, and it is load-bearing.

    `evolve/arbitrate.py` decides which belief survives using four ordered
    rules with stated reasons. A model there would produce a store whose
    contents depend on sampling, and "why do you think that?" would have no
    answer -- which is the question the whole provenance chain exists for.
    """
    raise NotImplementedError("implement arbitration_is_never_a_model")


def judging_the_exam(fixtures: int) -> str:
    """Why the exam is scored by string matching rather than by a model."""
    raise NotImplementedError("implement judging_the_exam")


def main() -> None:
    import json
    import pathlib

    fixtures = len(
        json.loads(
            pathlib.Path("capstone/fixtures/llm_responses.json").read_text()
        )
    )

    print(f"   {'site':24}{'role':13}{'bounded':>9}{'vs gold':>9}"
          f"{'repro':>7}{'safe':>7}")
    for use in uses():
        print(f"   {use.site:24}{use.role.value:13}"
              f"{use.bounded_output!s:>9}{use.checked_against_gold!s:>9}"
              f"{use.reproducible!s:>7}{use.safe!s:>7}")

    judgements = sum(1 for u in uses() if u.role is Role.JUDGEMENT)
    print(f"\n   model calls that are judgements: {judgements} of {len(uses())}")
    print(f"   fixtures backing them: {fixtures}")
    print(f"\n   {arbitration_is_never_a_model()}")
    print(f"\n   {judging_the_exam(fixtures)}")


if __name__ == "__main__":
    main()
