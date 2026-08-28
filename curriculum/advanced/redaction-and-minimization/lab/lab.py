"""Lab: store less on purpose, and measure what less costs.

    uv run python curriculum/advanced/redaction-and-minimization/lab/lab.py
"""

from __future__ import annotations

import re
from enum import Enum

from memlab.privacy.classify import Kind
from memlab.types import Memory


class Level(str, Enum):
    FULL = "full"
    COARSE = "coarse"
    TOKENISED = "tokenised"


# Per-kind coarsening. Each entry throws away a different thing, because
# "less precise" is not one operation: a city is a useful address, and there
# is no useful half of a phone number.
_COARSE: dict[Kind, tuple[re.Pattern, str]] = {
    Kind.ADDRESS: (re.compile(r"lives at [\w\s]+?,\s*(\w+)", re.IGNORECASE), r"lives in \1"),
    Kind.PHONE: (re.compile(r"\b0\d{4}\s?\d{6}\b"), "on file"),
    # Drops the diagnosis *event* and keeps the condition: "was diagnosed
    # with X last week" carries a date and a clinical encounter that a
    # question about food does not need.
    Kind.HEALTH: (
        re.compile(r"\bwas diagnosed with an?\b", re.IGNORECASE),
        "has a",
    ),
}

_TOKEN = {
    Kind.ADDRESS: "<address>",
    Kind.PHONE: "<phone>",
    Kind.HEALTH: "<health condition>",
    Kind.THIRD_PARTY_HEALTH: "<third party>",
}


def redact(memory: Memory, level: Level) -> Memory:
    """Rewrite a memory's content at the given level of detail.

    Content-addressed ids change when content changes, which is correct and
    load-bearing: a redacted memory is a different record, and pretending
    otherwise would let a full-detail copy and a redacted one share an id.
    """
    raise NotImplementedError("implement redact")


def _token(memory: Memory, kind: Kind) -> str:
    """Keep the subject and the shape; drop the value."""
    subject = memory.content.split()[0]
    return f"{subject} — {_TOKEN[kind]}"


def apply(memories: list[Memory], level: Level, kinds: set[Kind]) -> list[Memory]:
    """Redact the selected kinds; leave everything else alone."""
    raise NotImplementedError("implement apply")


SELECTIONS = [
    ("all four", set(Kind)),
    ("contact only", {Kind.ADDRESS, Kind.PHONE}),
    ("health only", {Kind.HEALTH}),
]


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.eval.exam import exam_answer
    from memlab.pipeline import at
    from memlab.privacy.classify import scan
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-redact.jsonl")
    store.clear()
    ingest(store, scope, at("A3"))
    memories = store.all()

    seen = set()
    for finding in scan(memories):
        if finding.kind in seen:
            continue
        seen.add(finding.kind)
        print(f"   {finding.kind.value}")
        for level in Level:
            print(f"      {level.value:10} {redact(finding.memory, level).content[:58]}")

    print(f"\n   {'level':12}{'kinds':16}{'exam':>7}")
    for level in Level:
        for label, kinds in SELECTIONS:
            out = apply(memories, level, kinds)
            print(f"   {level.value:12}{label:16}"
                  f"{exam_answer(out, scope).is_correct!s:>7}")

    health = next(f.memory for f in scan(memories) if "diagnosed" in f.memory.content)
    print(f"\n   redaction changes the id: "
          f"{health.id != redact(health, Level.COARSE).id}")


if __name__ == "__main__":
    main()
