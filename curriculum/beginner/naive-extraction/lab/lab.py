"""Lab: extraction caps everything downstream.

Run the naive extractor over the whole corpus, then audit what it produced
against ground truth. The interesting findings are things that are ABSENT.

    uv run python curriculum/beginner/naive-extraction/lab/lab.py
"""
from __future__ import annotations

from memlab.extract.naive import extract
from memlab.fixtures import load_gold, load_turns
from memlab.types import Memory, MemoryType, Scope

PII_MARKERS = ("Halloway Road", "07700", "gluten intolerance")


def audit_against_gold(memories: list[Memory], gold: dict) -> dict[str, list[str]]:
    """TODO: return findings keyed by 'missing_state', 'ungated_pii',
    'unhonoured_deletion'.

    - missing_state: is there any memory saying Priya WORKS AT Calico Systems?
      List the Calico memories that do exist if not.
    - ungated_pii: any memory containing a PII_MARKER.
    - unhonoured_deletion: a memory recording the request to forget the address,
      while the address itself is still present.
    """
    raise NotImplementedError("implement audit_against_gold")


def type_histogram(memories: list[Memory]) -> dict[str, int]:
    return {t.value: sum(1 for m in memories if m.type is t) for t in MemoryType}


def main() -> None:
    scope = Scope(user="priya")
    turns = [t for t in load_turns(user_only=True) if t["session"] < 14]

    memories: list[Memory] = []
    for turn in turns:
        memories.extend(extract(turn, scope))

    print(f"{len(turns)} turns -> {len(memories)} memories")
    for t, n in type_histogram(memories).items():
        if n:
            print(f"  {t:<11} {n:>3}")

    print("\naudit:")
    for kind, items in audit_against_gold(memories, load_gold()).items():
        print(f"\n  [{kind}]")
        for i in items:
            print(f"    - {i}")


if __name__ == "__main__":
    main()
