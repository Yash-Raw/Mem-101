"""Lab: most turns are not questions.

    uv run python curriculum/intermediate/retrieval-triggers/lab/lab.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass

QUESTION_MARK = re.compile(r"\?")

# Asking the store for something it already knows.
RECALL = ("remind me", "what did i", "do you remember", "what do you know",
          "where do i", "what should i", "who is", "run my", "how do i")

# Interrogative punctuation over new information. These belong on the write path.
INSTRUCTION = ("from now on", "can you keep", "please keep", "going forward",
               "stop ", "instead")
CORRECTION = ("remember?", "i told you", "i already said", "no,", "actually")


@dataclass
class Trigger:
    retrieve: bool
    reason: str


def decide(text: str) -> Trigger:
    """TODO: should this turn consult memory?

    Order is the policy. Check CORRECTION and INSTRUCTION first -- both can
    carry question marks, and retrieving for them is how an assistant argues
    with a user who is correcting it. Then RECALL, then a question mark, then
    treat it as a statement.

    Return Trigger(retrieve, reason). The reason is what makes the decision
    auditable.
    """
    raise NotImplementedError("implement decide")


def should_retrieve(text: str) -> bool:
    return decide(text).retrieve


def main() -> None:
    from collections import Counter

    from memlab.fixtures import load_turns

    turns = load_turns(user_only=True)
    decisions = [(t, decide(t["text"])) for t in turns]
    n = sum(1 for _, d in decisions if d.retrieve)

    print(f"{n} of {len(turns)} turns consult memory  "
          f"({1 - n / len(turns):.0%} of Beginner's retrievals were needless)\n")
    for reason, count in Counter(d.reason for _, d in decisions).most_common():
        print(f"  {count:>2}  {reason}")

    print("\nthe turns that do retrieve:")
    for turn, d in decisions:
        if d.retrieve:
            print(f"  s{turn['session']:<3} {turn['text'][:56]}")

    print("\nand two that look like questions and are not:")
    for turn, d in decisions:
        if not d.retrieve and "?" in turn["text"]:
            print(f"  s{turn['session']:<3} [{d.reason}]")
            print(f"       {turn['text'][:62]}")


if __name__ == "__main__":
    main()
