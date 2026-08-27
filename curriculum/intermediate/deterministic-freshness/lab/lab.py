"""Lab: four rules, in an order that matters.

    uv run python curriculum/intermediate/deterministic-freshness/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.types import Memory

# Below this, a claim is hearsay and loses to a first-party statement whatever
# its date. Priya's colleague speculating that she is relocating does not beat
# Priya's own address.
FIRST_PARTY = 0.5


@dataclass
class Verdict:
    winner: Memory
    loser: Memory
    rule: str

    @property
    def reason(self) -> str:
        return f"{self.rule}: kept {self.winner.content!r}"


def _when(memory: Memory):
    return memory.happened_at or memory.recorded_at


def arbitrate(a: Memory, b: Memory) -> Verdict:
    """TODO: decide which belief survives. Four rules, first-to-discriminate wins.

      1. authority  -- a relayed claim (< FIRST_PARTY) never beats a
                       first-party one, whatever its date. This one saves the
                       Berlin case, and only if it runs FIRST.
      2. recency    -- later wins, by EVENT time (_when), not ingestion time.
      3. confidence -- tiebreak within the same moment.
      4. stable     -- sort by id, so the same input always gives the same
                       answer. Arbitrary is fine; varying is not.

    Name the rule on the Verdict -- an unexplainable retirement is a bug.
    """
    raise NotImplementedError("implement arbitrate")


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.evolve.conflict import detect
    from memlab.evolve.operations import Operation, decide_all
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-arbitrate.jsonl")
    store.clear()
    ingest(store, scope, at("I3"))

    print(f"{'rule':<12} retired")
    for d in decide_all(detect(store.all(), scope)):
        if d.operation is Operation.UPDATE and d.verdict:
            print(f"{d.verdict.rule:<12} {d.verdict.loser.content[:58]}")

    print("\nSeven on recency, one on authority.")
    print("The one on authority is why that rule sits first.")


if __name__ == "__main__":
    main()
