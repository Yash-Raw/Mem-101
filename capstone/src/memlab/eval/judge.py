"""Where a model is asked to decide, and what that costs an evaluation.

This course uses a model in exactly three places, and only one of them is a
judgement:

    extract/naive.py     turn -> candidate memories        generation
    extract/pipeline.py  turn -> candidate memories        generation
    evolve/conflict.py   two beliefs -> a relation         JUDGEMENT

`deterministic-freshness` split that deliberately: the model says *these two
disagree*, and rules say *this one wins*. The split is the whole argument --
detection is a language question and arbitration is a policy, and handing the
policy to a model means the same pair can be decided differently on two runs
with nothing recording why.

Which is the case against LLM-as-judge for *evaluation* too, and it is
sharper there. A judge scoring the exam is a second system with its own
failure modes, no ground truth of its own, and no audit trail -- and when it
disagrees with the answer key, nothing says which is wrong.

What makes `conflict.classify` acceptable is that its output is one of four
labels, checked against `gold.yml`, and fixture-backed so it is reproducible.
Take away any of the three and it becomes the thing this lesson warns about.
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
    return [
        Use("extract/naive.py", Role.GENERATION, False, False, True),
        Use("extract/pipeline.py", Role.GENERATION, False, False, True),
        Use("evolve/conflict.py", Role.JUDGEMENT, True, True, True),
    ]


def arbitration_is_never_a_model() -> str:
    """Stated as a rule because it is one, and it is load-bearing.

    `evolve/arbitrate.py` decides which belief survives using four ordered
    rules with stated reasons. A model there would produce a store whose
    contents depend on sampling, and "why do you think that?" would have no
    answer -- which is the question the whole provenance chain exists for.
    """
    return (
        "detection is a language question and may be a model; arbitration is "
        "a policy and must not be, because its output changes what is "
        "believed and has to be explainable"
    )


def judging_the_exam(fixtures: int) -> str:
    """Why the exam is scored by string matching rather than by a model."""
    return (
        f"a judge is a second system with no ground truth of its own; when it "
        f"disagrees with the key nothing says which is wrong. The exam is "
        f"checked against {fixtures} reviewable fixtures instead"
    )
