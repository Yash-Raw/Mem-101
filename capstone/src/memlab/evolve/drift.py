"""What happens when you summarise a summary.

Compaction is not a one-off. A long-running memory layer compacts, and then
compacts the result, and the tempting implementation takes yesterday's summary
as today's input -- it is cheaper, and the sources may be archived by then.

Each round is lossy, and the loss compounds against a shrinking base. Round two
does not lose 20% of the original; it loses 20% of what round one left. Facts
disappear permanently and nothing records that they existed, because the only
thing that knew was the input you just replaced.

The fix is `derived_from`. Re-derive from the anchors every time rather than
from the last summary, and compaction becomes idempotent: summarising twice at
the same ratio gives the same result as summarising once.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..types import Memory

SEPARATOR = "; "


@dataclass
class DriftPoint:
    round: int
    claims: int
    recoverable: float          # fraction of ORIGINAL claims still present
    chars: int


def claims_in(text: str) -> list[str]:
    body = text.split(": ", 1)[-1] if text.startswith("Summary of ") else text
    return [c.strip() for c in body.split(SEPARATOR) if c.strip()]


def compact(text: str, keep: float = 0.7) -> str:
    """Drop the tail. A plausible policy, and the one that does the damage.

    Any real compaction has to drop something; which end it drops is a policy
    choice, and every choice loses information the next round cannot recover.
    """
    parts = claims_in(text)
    n = max(1, int(len(parts) * keep))
    return SEPARATOR.join(parts[:n])


def drift_curve(sources: list[Memory], rounds: int = 4, keep: float = 0.7) -> list[DriftPoint]:
    """Summarise the summary, repeatedly. The naive loop."""
    original = [m.content for m in sources]
    text = SEPARATOR.join(original)

    points = [DriftPoint(0, len(original), 1.0, len(text))]
    for r in range(1, rounds + 1):
        text = compact(text, keep)
        present = claims_in(text)
        recoverable = sum(1 for c in original if c in present) / len(original)
        points.append(DriftPoint(r, len(present), recoverable, len(text)))
    return points


def rederive_curve(sources: list[Memory], rounds: int = 4, keep: float = 0.7) -> list[DriftPoint]:
    """Re-derive from the anchors every round. The fix."""
    original = [m.content for m in sources]
    points = [DriftPoint(0, len(original), 1.0, len(SEPARATOR.join(original)))]
    for r in range(1, rounds + 1):
        # Always from the sources, never from the previous output.
        text = compact(SEPARATOR.join(original), keep)
        present = claims_in(text)
        recoverable = sum(1 for c in original if c in present) / len(original)
        points.append(DriftPoint(r, len(present), recoverable, len(text)))
    return points


def is_idempotent(sources: list[Memory], keep: float = 0.7) -> bool:
    """Compacting twice should equal compacting once. Only re-derivation is."""
    curve = rederive_curve(sources, rounds=2, keep=keep)
    return curve[1].claims == curve[2].claims
