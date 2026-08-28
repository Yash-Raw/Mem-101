"""Which memories carry personal data, and what that should change.

`gold.yml` marks four items and all four are in the store:

    address              47 Halloway Road, Bristol      stored
    phone                07700 900412                   stored
    health               gluten intolerance             stored (2 memories)
    third_party_health   Sam is a nurse                 stored

There is a write-path gate already -- `extract/gate.py` -- and it decides
*memory-worthiness*, not sensitivity: it drops scratch-tier activity and keeps
everything else. No stage has ever asked whether a candidate is personal data.

The obvious response is to block PII at the gate, and it breaks the system.
`gluten intolerance` is health data and it is one of the four facts the exam
requires. A policy that protects it by not storing it has protected the user
from an answer they asked for.

So the classification is not a permission. It is a *label* that later stages
consult: redaction chooses what to store, access control chooses who may read
it, and deletion needs to know what it is looking for.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from ..types import Memory


class Kind(str, Enum):
    ADDRESS = "address"
    PHONE = "phone"
    HEALTH = "health"
    THIRD_PARTY_HEALTH = "third_party_health"


# Patterns rather than a model: a false negative here is a missed label, and a
# false positive is a fact the system refuses to remember. Both are visible,
# and neither is worth a nondeterministic classifier on the write path.
PATTERNS: dict[Kind, re.Pattern] = {
    Kind.ADDRESS: re.compile(r"\blives at\b|\b\d+\s+\w+\s+(?:Road|Street|Lane)\b", re.IGNORECASE),
    Kind.PHONE: re.compile(r"\b0\d{4}\s?\d{6}\b|\bphone number\b", re.IGNORECASE),
    Kind.HEALTH: re.compile(r"\bintolerance\b|\ballerg|\bdiagnosed\b", re.IGNORECASE),
}

# Health facts about someone who is not the account holder. Detected by the
# entity link I2 populates -- which is the only thing that distinguishes
# "her nurse" from "she is a nurse" once the sentence is a memory.
THIRD_PARTY_HEALTH = re.compile(r"\bnurse\b|\bcharge nurse\b", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    memory: Memory
    kind: Kind

    @property
    def about_the_user(self) -> bool:
        return self.kind is not Kind.THIRD_PARTY_HEALTH


def classify(memory: Memory) -> Kind | None:
    """The personal-data label for one memory, if any."""
    if memory.entities and THIRD_PARTY_HEALTH.search(memory.content):
        return Kind.THIRD_PARTY_HEALTH
    for kind, pattern in PATTERNS.items():
        if pattern.search(memory.content):
            return kind
    return None


def scan(memories: list[Memory]) -> list[Finding]:
    """Every memory carrying personal data, labelled."""
    return [
        Finding(memory=m, kind=classify(m))
        for m in memories
        if classify(m) is not None
    ]


def blocked_by(findings: list[Finding], kinds: set[Kind]) -> list[Memory]:
    """What a block-on-these-kinds policy would refuse to store."""
    return [f.memory for f in findings if f.kind in kinds]
