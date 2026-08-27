"""Lab: the type is an update rule, not a label.

Route the corpus, then prove the claim this lesson rests on: of the four memory
types, only ONE is capable of holding a contradiction.

    uv run python curriculum/beginner/memory-taxonomy/lab/lab.py
"""
from __future__ import annotations

from collections import Counter

from memlab.app.chat import ingest
from memlab.store.jsonl import JsonlStore
from memlab.types import Memory, MemoryType, Scope

SUBJECTS = {
    "employer": ("Northwind", "Calico", "data engineer", "staff engineer"),
    "diet": ("vegetarian", "meat", "fish", "pescatarian", "gluten"),
    "beverage": ("coffee", "tea"),
    "response_style": ("detailed explanations", "shorter answers"),
    "commute": ("cycle", "train", "commute"),
}


def subject_of(m: Memory) -> str | None:
    for subject, keywords in SUBJECTS.items():
        if any(k in m.content for k in keywords):
            return subject
    return None


def can_contradict(m: Memory) -> bool:
    """TODO: return True only for memories that CAN hold a contradiction.

    Ask: does this memory claim something is true *now*? An episode says
    "X happened at T" and stays true forever. A procedure is replaced
    wholesale rather than contradicted. Only one type is at risk.
    """
    raise NotImplementedError("implement can_contradict")


def contradiction_candidates(memories: list[Memory]) -> dict[str, list[Memory]]:
    """TODO: group contradictable memories by subject; keep groups with >1."""
    raise NotImplementedError("implement contradiction_candidates")


def main() -> None:
    store = JsonlStore("/tmp/memlab-taxonomy.jsonl")
    store.clear()
    ingest(store, Scope(user="priya"))
    memories = store.all()

    counts = Counter(m.type.value for m in memories)
    print(f"{len(memories)} memories routed:")
    for t in MemoryType:
        print(f"  {t.value:<11} {counts.get(t.value, 0):>3}")

    at_risk = [m for m in memories if can_contradict(m)]
    print(f"\n{len(at_risk)} of {len(memories)} can hold a contradiction.")
    print(f"The other {len(memories) - len(at_risk)} cannot, by type alone.\n")

    for subject, group in sorted(contradiction_candidates(memories).items()):
        print(f"  {subject}:")
        for m in group:
            when = m.happened_at.date().isoformat() if m.happened_at else "undated"
            print(f"    [{when}] {m.content}")
    print("\nEvery one of these is live. Nothing retires anything yet.")


if __name__ == "__main__":
    main()
