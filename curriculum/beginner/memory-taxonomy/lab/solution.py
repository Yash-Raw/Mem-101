"""Reference solution."""
from __future__ import annotations

from memlab.types import Memory, MemoryType

# Crude subject keys. A real system resolves entities and slots; this is enough
# to prove the point, and its crudeness is itself the argument for Level 2.
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
    """Only a claim about *now* can be contradicted by another claim about now."""
    return m.type is MemoryType.SEMANTIC and m.is_live


def contradiction_candidates(memories: list[Memory]) -> dict[str, list[Memory]]:
    """Live semantic memories that claim to describe the same subject."""
    groups: dict[str, list[Memory]] = {}
    for m in memories:
        if not can_contradict(m):
            continue
        if (s := subject_of(m)) is not None:
            groups.setdefault(s, []).append(m)
    return {s: ms for s, ms in groups.items() if len(ms) > 1}
