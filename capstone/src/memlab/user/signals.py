"""What the user's behaviour says that their statements do not.

Every memory in this store was extracted from something the user *asserted*.
The transcript also contains them reacting to what the assistant said, and
those reactions are labelled data nobody is collecting.

The clearest one is in session 9:

    assistant   How are you finding it compared to your work at Northwind Labs?
    user        I left Northwind last month, remember? I'm at Calico now.

That is a negative example with a target attached. The assistant used a
belief, the user rejected it, and the belief is identifiable from the
assistant's own turn. Today the store records none of it -- `access_count`
is 0 on all 37 memories, so nothing knows any belief has ever been used, let
alone used and corrected.

`sleep-time-compute` measured the other half of this: session 9 is turn 16,
inside the eleven-turn window where a deferred store still believes Northwind.
**The one correction in the corpus is the user paying that bill.**
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..types import Memory

# Deliberately narrow. A broad pattern turns every "no" into a correction --
# including "no meat", which is a dietary fact and not a complaint about the
# assistant. Precision matters more than recall here: a false correction
# demotes a belief that was right.
_CORRECTION = re.compile(
    r"\bremember\?|\bI (?:said|told you)\b|\bthat'?s (?:not|wrong)\b|\bactually,? (?:no|I)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Correction:
    """A user turn rejecting what the assistant just said."""

    session: int
    assistant_said: str
    user_replied: str
    target: Memory | None = None

    @property
    def attributed(self) -> bool:
        return self.target is not None


def corrections(turns: list[dict]) -> list[Correction]:
    """User turns that reject the assistant's immediately preceding turn.

    The pairing is what makes this a *signal* rather than a sentiment: a
    correction with no assistant turn before it is the user changing their
    mind, which is an ordinary write, not evidence that a belief was wrong.
    """
    out = []
    for previous, turn in zip(turns, turns[1:], strict=False):
        if turn.get("role") != "user" or previous.get("role") != "assistant":
            continue
        if _CORRECTION.search(turn["text"]):
            out.append(
                Correction(
                    session=turn["session"],
                    assistant_said=previous["text"],
                    user_replied=turn["text"],
                )
            )
    return out


def attribute(correction: Correction, memories: list[Memory]) -> Correction:
    """Find the belief the assistant's turn used.

    Matched on content overlap with the assistant's own words, which is
    available and honest: the assistant said it, so the words are there. A
    retrieval log would be better and this course does not keep one -- which
    is itself the finding, and `memory-observability` is where it lands.
    """
    said = correction.assistant_said.lower()
    scored = [
        (sum(1 for w in _keywords(m.content) if w in said), m)
        for m in memories
    ]
    best, target = max(scored, key=lambda pair: pair[0], default=(0, None))
    return Correction(
        session=correction.session,
        assistant_said=correction.assistant_said,
        user_replied=correction.user_replied,
        target=target if best else None,
    )


def _keywords(content: str) -> list[str]:
    """Capitalised tokens and long words -- what a sentence is *about*."""
    return [
        w.strip(".,'?").lower()
        for w in content.split()
        if w[:1].isupper() or len(w.strip(".,'?")) > 6
    ]


def used(memories: list[Memory]) -> int:
    """How many beliefs record ever having been retrieved."""
    return sum(1 for m in memories if m.access_count)
