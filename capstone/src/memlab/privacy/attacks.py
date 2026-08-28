"""Four attacks on a memory layer, and which defences this course already has.

Every one of these is a mechanism from an earlier module, re-read as a threat
model rather than a quality problem. That re-reading is the lesson: nothing
new is built here, and the measurement is which of the four are covered.

    poisoning       write a false belief that outranks the truth
    injection       get instructions stored as facts
    cross-user      read another tenant's memories
    extraction      recover a deleted or withheld value from what remains

The uncomfortable result is that the defences were built for other reasons --
arbitration for correctness, scopes for relevance, the write policy for a
clock bug -- and the one attack with no accidental defence is the one nobody
mentions.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Attack(str, Enum):
    POISONING = "poisoning"
    INJECTION = "injection"
    CROSS_USER = "cross-user read"
    EXTRACTION = "extraction"


@dataclass(frozen=True)
class Defence:
    attack: Attack
    mechanism: str
    built_for: str
    covered: bool
    residual: str


def survey() -> list[Defence]:
    """What stands between each attack and the store, and why it exists."""
    return [
        Defence(
            attack=Attack.POISONING,
            mechanism="claim-scoped trust into arbitration (A3.3)",
            built_for="deciding which of two honest beliefs is current",
            covered=True,
            residual=(
                "only for claims that name a modelled slot; an unnameable "
                "claim is never arbitrated at all"
            ),
        ),
        Defence(
            attack=Attack.INJECTION,
            mechanism="the durability gate routes imperatives away (I1)",
            built_for="keeping requests out of the belief store",
            covered=True,
            residual=(
                "matches two phrasings; a request worded as a fact is stored "
                "as one"
            ),
        ),
        Defence(
            attack=Attack.CROSS_USER,
            mechanism="scope filter, plus leak_check as an invariant (A3.4)",
            built_for="relevance -- ranking across tenants returns noise",
            covered=True,
            residual="the assertion fires only if the filter itself is broken",
        ),
        Defence(
            attack=Attack.EXTRACTION,
            mechanism="none",
            built_for="",
            covered=False,
            residual=(
                "a deleted value can be inferred from what was derived from "
                "it, and nothing tracks that direction"
            ),
        ),
    ]


def uncovered(defences: list[Defence]) -> list[Defence]:
    return [d for d in defences if not d.covered]


def accidental(defences: list[Defence]) -> list[Defence]:
    """Defences built for a reason other than security.

    All of them, here. A control that exists as a side effect is a control
    nobody is maintaining as a control -- it will be refactored for the
    reason it was built, by someone who does not know it is load-bearing
    twice.
    """
    return [d for d in defences if d.covered and "securit" not in d.built_for]
