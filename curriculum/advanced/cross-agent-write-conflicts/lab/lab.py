"""Lab: when two writers claim the same attribute.

    uv run python curriculum/advanced/cross-agent-write-conflicts/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.evolve.arbitrate import FIRST_PARTY
from memlab.types import Memory, Scope


@dataclass(frozen=True)
class CrossWriter:
    """A candidate pair whose two memories came from different writers."""

    a: Memory
    b: Memory
    slot: str

    @property
    def writers(self) -> tuple[str, str]:
        return (self.a.provenance.speaker, self.b.provenance.speaker)

    @property
    def agent_versus_agent(self) -> bool:
        return bool(self.a.scope.agent) and bool(self.b.scope.agent)


def cross_writer(memories: list[Memory], scope: Scope) -> list[CrossWriter]:
    """Candidate pairs where the two claims have different authors.

    Run this over the *unconsolidated* store. After reconciliation the losers
    are retired and excluded from candidate generation, so the same call
    returns nothing and the absence looks like a property of the corpus rather
    than of when you asked.
    """
    raise NotImplementedError("implement cross_writer")


def decided_by(a: Memory, b: Memory) -> tuple[str, str, str, str]:
    """The rule and winner under raw authority, then under per-claim trust."""
    raise NotImplementedError("implement decided_by")


def above_the_line(memory: Memory) -> bool:
    """Whether rule 1 will treat this writer as first-party at all."""
    return memory.provenance.authority >= FIRST_PARTY


USER_SAYS = ("Priya is pescatarian", "user", 1.0, None)
RIVALS = [
    ("travel-agent 0.3, newer",
     "Priya's colleague mentioned she is relocating", "travel-agent", 0.3),
    ("calendar-agent 0.9, newer",
     "Priya is vegetarian", "calendar-agent", 0.9),
]


def _memory(content, speaker, authority, agent, when):
    from memlab.types import MemoryType, Provenance

    return Memory(
        content=content,
        type=MemoryType.SEMANTIC,
        scope=Scope(user="priya", agent=agent),
        happened_at=when,
        provenance=Provenance(
            source_id=f"{speaker}:x", speaker=speaker, authority=authority
        ),
        confidence=authority,
    )


def main() -> None:
    from datetime import UTC, datetime

    from memlab.app.chat import _agent_memories
    from memlab.fixtures import load_turns
    from memlab.pipeline import at

    scope = Scope(user="priya")
    pipeline = at("A3")

    # Unconsolidated on purpose: reconciliation retires the losers, and a
    # retired memory is not a conflict candidate.
    raw = [
        m
        for turn in load_turns(user_only=True)
        if turn["session"] < 14
        for m in pipeline.extract(turn, scope)
    ] + _agent_memories(scope)

    pairs = cross_writer(raw, scope)
    print(f"cross-writer candidate pairs: {len(pairs)}\n")
    for pair in pairs:
        print(f"   [{pair.slot}] {pair.writers}  "
              f"agent-vs-agent={pair.agent_versus_agent}")

    old, new = datetime(2025, 8, 2, tzinfo=UTC), datetime(2026, 6, 1, tzinfo=UTC)
    mine = _memory(*USER_SAYS[:3], USER_SAYS[3], old)
    print()
    for label, content, speaker, authority in RIVALS:
        rival = _memory(content, speaker, authority, speaker, new)
        rule_a, winner_a, rule_t, winner_t = decided_by(mine, rival)
        print(f"   {label:28} above_the_line={above_the_line(rival)}")
        print(f"      by authority: rule={rule_a:10} winner={winner_a}")
        print(f"      by trust    : rule={rule_t:10} winner={winner_t}")


if __name__ == "__main__":
    main()
