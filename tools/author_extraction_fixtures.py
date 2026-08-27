#!/usr/bin/env python3
"""Author the naive extractor's fixtures by hand. No model is called.

These are what a competent-but-naive LLM extractor really returns: it reads one
turn at a time, with no view of what is already stored. So it happily creates a
third person called "Sammy", records a deletion request as a memory instead of
acting on it, and -- the one that matters most -- writes the job change as two
EPISODIC events rather than a semantic `employer` fact.

Every failure the Beginner track diagnoses is already latent right here.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "capstone" / "src"))

from memlab.extract.naive import SCHEMA, build_messages
from memlab.fixtures import load_turns
from memlab.llm.fake import register_fixture

S, E, P = "semantic", "episodic", "procedural"

EXTRACTIONS: dict[str, list[tuple[str, str]]] = {
    "Morning. I'm Priya": [
        ("Priya is a data engineer at Northwind Labs", S),
        ("Priya mostly does pipeline work", S),
    ],
    "Debugging a Spark job": [
        ("Priya is debugging a Spark job", E),
        ("Priya is vegetarian", S),
    ],
    "One more thing, I like detailed": [
        ("Priya prefers detailed explanations with reasoning", S),
    ],
    "My partner Sam is a nurse": [
        ("Priya's partner Sam is a nurse at St. Aubyn's", S),
        ("Priya is planning a trip around Sam's shift rota", E),
    ],
    "She works nights most of the month": [
        # The pronoun is never resolved. Stored exactly as spoken.
        ("She works nights most of the month", S),
    ],
    "Samira got a promotion": [
        # A second person is born. Nothing connects Samira to Sam.
        ("Samira got a promotion to charge nurse", E),
        ("Samira is a charge nurse", S),
    ],
    "Can you remind me what I said": [],
    "I don't drink coffee": [
        ("Priya does not drink coffee", S),
        ("Priya drinks tea", S),
    ],
    "We moved. New place is": [
        # PII walks straight in. No classification, no gate, no consent check.
        ("Priya moved house", E),
        ("Priya's address is 47 Halloway Road, Bristol", S),
        ("Priya's phone number is 07700 900412", S),
    ],
    "Sammy's commute got worse": [
        # A third person.
        ("Sammy's commute got worse", E),
        ("Priya's new flat is bigger", S),
    ],
    "Here's how I do my weekly report": [
        (
            (
                "Priya's weekly report process: pull pipeline metrics from the warehouse, "
                "diff against last week, flag anything over 15% drift, write it up in the "
                "shared doc, in that order"
            ),
            P,
        ),
    ],
    "The diff step matters most": [
        ("In Priya's weekly report, the diff step matters most", P),
    ],
    "Actually I've started eating fish": [
        # Three new facts. None of them touch "Priya is vegetarian", still live.
        ("Priya eats fish", S),
        ("Priya does not eat meat", S),
        ("Priya is pescatarian", S),
    ],
    "Big news": [
        # THE critical one. The change is recorded as two events, never as the
        # state `employer = Calico Systems`. This is why the right answer to
        # session 14 ranks 18th out of 24.
        ("Priya is leaving Northwind Labs", E),
        ("Priya is starting at Calico Systems in January as a staff engineer", E),
    ],
    "It's a step up": [
        ("Priya's new role involves more architecture and less firefighting", S),
    ],
    "First week done at the new place": [
        ("Priya completed her first week at the new job", E),
    ],
    "I left Northwind last month": [
        ("Priya left Northwind Labs last month", E),
        ("Priya is at Calico now", S),
    ],
    "Honestly the coffee machine": [
        # Flatly contradicts session 4. Both stay live.
        ("Priya drinks three coffees a day", S),
    ],
    "Also can you keep answers shorter": [
        # Contradicts session 1. Both stay live.
        ("Priya prefers shorter answers", S),
    ],
    "Before the move I used to cycle": [
        ("Priya used to cycle to work before the move", E),
        ("Priya's commute is 40 minutes by train", S),
    ],
    "Sam's still on nights": [
        ("Sam still works nights", S),
    ],
    "I was diagnosed with a gluten": [
        ("Priya has a gluten intolerance", S),
        ("Priya was diagnosed with a gluten intolerance last week", E),
    ],
    "Run my weekly report process": [],
    "And actually — forget my old address": [
        # The request is filed as a memory. Nothing deletes anything.
        ("Priya asked to forget her old address", E),
    ],
    "Quick one: where do I work": [],
}


def main() -> int:
    turns = load_turns(user_only=True)
    written, unmatched = 0, []

    for turn in turns:
        match = next((k for k in EXTRACTIONS if turn["text"].startswith(k)), None)
        if match is None:
            unmatched.append(turn["text"][:60])
            continue
        payload = [{"content": c, "type": t} for c, t in EXTRACTIONS[match]]
        register_fixture(build_messages(turn["text"]), payload, SCHEMA)
        written += 1

    if unmatched:
        print("NO FIXTURE AUTHORED FOR:")
        for u in unmatched:
            print("   ", u)
        return 1

    total = sum(len(v) for v in EXTRACTIONS.values())
    print(f"authored {written} fixtures covering {len(turns)} user turns -> {total} memories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
