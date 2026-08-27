"""Lab: the type decides who can even be wrong.

    uv run python curriculum/intermediate/typed-memory-model/lab/lab.py
"""
from __future__ import annotations

from memlab.extract.router import RULES
from memlab.types import Memory


def can_contradict(memory: Memory) -> bool:
    """TODO: return True only for memories that can be made false by another.

    Read it off RULES -- do not re-derive the policy here. A retired memory
    cannot contradict anything either.
    """
    raise NotImplementedError("implement can_contradict")


def partition_by_conflict_risk(
    memories: list[Memory],
) -> tuple[list[Memory], list[Memory]]:
    """TODO: return (at risk, structurally safe)."""
    raise NotImplementedError("implement partition_by_conflict_risk")


def comparisons_avoided(memories: list[Memory]) -> tuple[int, int]:
    n = len(memories)
    at_risk, _ = partition_by_conflict_risk(memories)
    r = len(at_risk)
    return n * (n - 1) // 2, r * (r - 1) // 2


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.store.jsonl import JsonlStore
    from memlab.types import MemoryType, Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-typed.jsonl")
    store.clear()
    ingest(store, scope)
    memories = store.all()

    at_risk, safe = partition_by_conflict_risk(memories)
    print(f"{len(memories)} memories: {len(at_risk)} can contradict, {len(safe)} cannot\n")

    print("the rule table:")
    for t in MemoryType:
        r = RULES[t]
        print(f"  {t.value:<11} contradicts={r.can_contradict!s:<5} -> {r.on_conflict}")

    print("\ntwo pairs that look alike to similarity:\n")
    pairs = [
        ("Northwind Labs", "episodes -- both permanently true"),
        ("coffee", "semantic -- one of these must retire"),
    ]
    for needle, note in pairs:
        group = [m for m in memories if needle.split()[0].lower() in m.content.lower()]
        print(f"  {note}")
        for m in group[:3]:
            print(f"    [{m.type.value:<10} contradicts={can_contradict(m)}] {m.content[:50]}")
        print()

    naive, real = comparisons_avoided(memories)
    print(f"pairwise comparisons: {naive} naive -> {real} after typing")


if __name__ == "__main__":
    main()
