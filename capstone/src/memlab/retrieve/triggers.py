"""Should this turn consult memory at all?

Beginner retrieved on every turn. Measured against the corpus, that is wrong
about 88% of the time: **of 25 turns, 3 genuinely ask the system for
something.** The other 22 are Priya telling it things, which is the write
path's business.

Every needless retrieval costs a ranking pass and, worse, produces an answer:
if you always retrieve you always retrieve *something*, and that something
competes for the same five slots as a real recall.

The subtle part is that a question mark does not mean a question.

    "Can you keep answers shorter from now on?"   an INSTRUCTION
    "I left Northwind last month, remember?"      a CORRECTION
    "Where do I work and what should I not eat?"  a question

The first two are new information wearing interrogative punctuation. Retrieving
for them is how an assistant ends up arguing with a user who is correcting it.

The bias, where genuinely ambiguous, is toward retrieving: a needless retrieval
costs latency, and a missing one looks like amnesia -- and amnesia is the
failure users actually report.
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
    lowered = text.lower().strip()

    if any(cue in lowered for cue in CORRECTION):
        return Trigger(False, "correction -- new information, write path")
    if any(cue in lowered for cue in INSTRUCTION):
        return Trigger(False, "instruction -- new information, write path")
    if any(cue in lowered for cue in RECALL):
        return Trigger(True, "explicit recall")
    if QUESTION_MARK.search(lowered):
        return Trigger(True, "question")
    return Trigger(False, "statement -- write path")


def should_retrieve(text: str) -> bool:
    return decide(text).retrieve
