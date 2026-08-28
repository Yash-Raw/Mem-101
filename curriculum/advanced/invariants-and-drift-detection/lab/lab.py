"""Lab: one health call, and an invariant that could not fail.

    uv run python curriculum/advanced/invariants-and-drift-detection/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from memlab.types import Memory


class Kind(str, Enum):
    STRUCTURAL = "structural"
    POLICY = "policy"


@dataclass(frozen=True)
class Violation:
    invariant: str
    kind: Kind
    count: int
    detail: str = ""

    @property
    def holds(self) -> bool:
        return self.count == 0


def check(memories: list[Memory], scope) -> list[Violation]:
    """Every invariant this course established, in one pass."""
    raise NotImplementedError("implement check")


def failing(violations: list[Violation]) -> list[Violation]:
    raise NotImplementedError("implement failing")


def by_kind(violations: list[Violation], kind: Kind) -> list[Violation]:
    raise NotImplementedError("implement by_kind")


def main() -> None:
    from datetime import UTC, datetime

    from memlab.app import chat
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import MemoryType, Provenance, Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-invariants.jsonl")
    store.clear()
    ingest(store, scope, at("A3"))
    violations = check(store.all(), scope)

    print(f"   {'invariant':46}{'kind':12}{'count':>6}  holds")
    for violation in violations:
        print(f"   {violation.invariant:46}{violation.kind.value:12}"
              f"{violation.count:>6}  {violation.holds}")
    print(f"\n   structural: {len(by_kind(violations, Kind.STRUCTURAL))}   "
          f"policy: {len(by_kind(violations, Kind.POLICY))}")

    print()
    for profile in ("I8", "A1", "A3"):
        probe = JsonlStore(f"/tmp/memlab-invariants-{profile}.jsonl")
        probe.clear()
        ingest(probe, scope, at(profile))
        broken = failing(check(probe.all(), scope))
        print(f"   @{profile}: {len(broken)} failing  "
              f"{[(v.invariant, v.count) for v in broken]}")

    original = chat._agent_memories
    try:
        chat._agent_memories = lambda s: [
            *original(s),
            Memory(
                content="Priya works at Meridian",
                type=MemoryType.SEMANTIC,
                scope=Scope(user="priya"),
                happened_at=datetime(2027, 5, 16, tzinfo=UTC),
                provenance=Provenance(
                    source_id="t:z", speaker="travel-agent", authority=0.3
                ),
                confidence=0.3,
            ),
        ]
        rogue = JsonlStore("/tmp/memlab-invariants-rogue.jsonl")
        rogue.clear()
        ingest(rogue, scope, at("A3").with_stage(admit=None))
    finally:
        chat._agent_memories = original

    broken = failing(check(rogue.all(), scope))
    print(f"\n   unguarded future-dated write: {len(broken)} failing  "
          f"{[(v.invariant, v.count) for v in broken]}")

    stamps = [m.happened_at for m in rogue.all() if m.happened_at]
    whole_store = sum(
        1 for s in stamps if s > max(stamps) + timedelta(days=1)
    )
    print(f"   the same check against the whole store: {whole_store} failing")


if __name__ == "__main__":
    main()
