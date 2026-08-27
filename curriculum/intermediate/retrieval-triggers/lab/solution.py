"""Reference solution."""

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
