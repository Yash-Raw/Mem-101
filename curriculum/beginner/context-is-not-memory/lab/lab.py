"""Lab: truncation is not neutral.

Replaying the transcript means truncating it. Find out what truncation
systematically throws away.

    uv run python curriculum/beginner/context-is-not-memory/lab/lab.py
"""
from __future__ import annotations

from memlab.assemble.simple import estimate_tokens
from memlab.fixtures import load_turns

BUDGET = 250
FACTS = {
    "Northwind Labs": "employer (STALE)",
    "Calico Systems": "employer (CURRENT)",
    "vegetarian": "diet (baseline)",
    "fish": "diet (refinement)",
    "gluten": "diet (addition)",
}


def fit_to_budget(turns: list[dict], budget: int, newest_first: bool = False) -> list[dict]:
    """TODO: return the turns that fit in `budget` tokens.

    Steps:
      1. sort by timestamp -- oldest first, or newest first if the flag is set
      2. add whole turns, tracking cost with estimate_tokens(), until the next
         one would exceed the budget
      3. return them back in chronological order
    """
    raise NotImplementedError("implement fit_to_budget")


def report(label: str, kept: list[dict], all_turns: list[dict]) -> None:
    print(f"\n{label}: {len(kept)} of {len(all_turns)} turns fit in {BUDGET} tokens")
    text = " ".join(t["text"] for t in kept)
    for needle, name in FACTS.items():
        mark = "kept   " if needle in text else "DROPPED"
        print(f"    {mark}  {name}")


def main() -> None:
    turns = load_turns(user_only=True)
    total = sum(estimate_tokens(t["text"]) for t in turns)
    print(f"Priya's full history: {len(turns)} turns, ~{total} tokens")

    report("oldest-first", fit_to_budget(turns, BUDGET), turns)
    report("newest-first", fit_to_budget(turns, BUDGET, newest_first=True), turns)

    print("\nNeither ordering keeps both the current employer and the diet baseline.")
    print("No truncation strategy does. That is why extraction exists.")


if __name__ == "__main__":
    main()
