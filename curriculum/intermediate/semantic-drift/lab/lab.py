"""Lab: what summarising a summary costs.

    uv run python curriculum/intermediate/semantic-drift/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.types import Memory

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
    """TODO: keep the first `keep` fraction of claims, at least one.

    Dropping the tail is a policy, not a neutral act -- whatever you drop is
    what the next round cannot recover.
    """
    raise NotImplementedError("implement compact")


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
    """TODO: the fix -- compact the SOURCES every round, never the last output.

    One word differs from drift_curve. Find it, and note that the compression
    ratio is identical.
    """
    raise NotImplementedError("implement rederive_curve")


def is_idempotent(sources: list[Memory], keep: float = 0.7) -> bool:
    """Compacting twice should equal compacting once. Only re-derivation is."""
    curve = rederive_curve(sources, rounds=2, keep=keep)
    return curve[1].claims == curve[2].claims


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import get
    from memlab.store.jsonl import JsonlStore
    from memlab.types import MemoryType, Scope

    store = JsonlStore("/tmp/memlab-drift.jsonl")
    store.clear()
    ingest(store, Scope(user="priya"), get("intermediate"))
    sources = [m for m in store.all() if m.type is MemoryType.SEMANTIC and m.is_live]

    print(f"{len(sources)} source claims, keep=0.7 per round\n")
    print(f"{'round':>6}{'naive':>9}{'recoverable':>13}   |{'re-derived':>12}{'recoverable':>13}")
    for a, b in zip(drift_curve(sources), rederive_curve(sources)):
        print(f"{a.round:>6}{a.claims:>9}{a.recoverable:>12.0%}   |"
              f"{b.claims:>12}{b.recoverable:>12.0%}")

    print(f"\nre-derivation is idempotent: {is_idempotent(sources)}")
    print("The naive loop is not -- so your data depends on how often the job ran.")


if __name__ == "__main__":
    main()
