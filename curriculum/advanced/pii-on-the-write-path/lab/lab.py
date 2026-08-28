"""Lab: label personal data, and measure what blocking it costs.

    uv run python curriculum/advanced/pii-on-the-write-path/lab/lab.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from memlab.types import Memory


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
    raise NotImplementedError("implement classify")


def scan(memories: list[Memory]) -> list[Finding]:
    """Every memory carrying personal data, labelled."""
    raise NotImplementedError("implement scan")


def blocked_by(findings: list[Finding], kinds: set[Kind]) -> list[Memory]:
    """What a block-on-these-kinds policy would refuse to store."""
    raise NotImplementedError("implement blocked_by")


POLICIES = [
    ("block nothing", set()),
    ("block all four kinds", set(Kind)),
    ("block contact details only", {Kind.ADDRESS, Kind.PHONE}),
    ("block third-party health only", {Kind.THIRD_PARTY_HEALTH}),
]


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.eval.exam import exam_answer
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-pii.jsonl")
    store.clear()
    ingest(store, scope, at("A3"))
    memories = store.all()

    findings = scan(memories)
    print(f"memories carrying personal data: {len(findings)} of {len(memories)}\n")
    for finding in findings:
        print(f"   {finding.kind.value:20} user={finding.about_the_user}  "
              f"{finding.memory.content[:52]}")

    print(f"\n   {'policy':32}{'blocked':>9}{'store':>7}{'exam':>7}")
    for label, kinds in POLICIES:
        dropped = {m.id for m in blocked_by(findings, kinds)}
        kept = [m for m in memories if m.id not in dropped]
        print(f"   {label:32}{len(dropped):>9}{len(kept):>7}"
              f"{exam_answer(kept, scope).is_correct!s:>7}")


if __name__ == "__main__":
    main()
