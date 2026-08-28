"""Lab: three tactics against a measured profile.

    uv run python curriculum/advanced/caching-batching-routing/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tactic:
    name: str
    applies: bool
    saving: str
    why: str


def assess(write_calls: int, write_embeds: int, read_calls: int) -> list[Tactic]:
    """What each tactic is worth against a measured profile."""
    raise NotImplementedError("implement assess")


def headroom(tactics: list[Tactic]) -> tuple[int, int]:
    """(tactics that apply, total considered)."""
    raise NotImplementedError("implement headroom")


def already_shipped(tactics: list[Tactic]) -> list[str]:
    """The ones this course built before it had a cost lesson."""
    raise NotImplementedError("implement already_shipped")


WRITE_CALLS, WRITE_EMBEDS, READ_CALLS = 48, 38, 0


def main() -> None:
    from memlab.fixtures import load_turns

    tactics = assess(WRITE_CALLS, WRITE_EMBEDS, READ_CALLS)
    print(f"   {'tactic':36}{'applies':>9}  saving")
    for tactic in tactics:
        print(f"   {tactic.name:36}{tactic.applies!s:>9}  {tactic.saving}")

    applies, total = headroom(tactics)
    print(f"\n   apply: {applies} of {total}")
    print(f"   already shipped: {already_shipped(tactics)}")

    turns = [t for t in load_turns(user_only=True) if t["session"] < 14]
    keys = {t["text"] for t in turns}
    print(f"\n   completion cache over {len(turns)} turns: "
          f"{len(keys)} distinct keys, {len(turns) - len(keys)} hits")


if __name__ == "__main__":
    main()
