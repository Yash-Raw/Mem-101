"""Lab: decide what survives the session.

    uv run python curriculum/beginner/session-vs-longterm/lab/lab.py
"""
from __future__ import annotations

from memlab.types import Memory, Tier

EXPLICIT = ("keep that in mind", "memorise", "from now on", "filing that away", "always in that order")
ACTIVITY = ("debugging", "completed her first week", "planning a trip", "is leaving")
IMPERATIVE = ("asked to forget", "asked to delete")


def promotion_tier(memory: Memory, turn_text: str = "") -> Tier:
    """TODO: return the tier this memory belongs in.

    Rules first, in roughly this priority order:
      1. an EXPLICIT marker in the originating turn  -> LONG_TERM
      2. an IMPERATIVE ("asked to forget")           -> SCRATCH, it is not a fact
      3. a procedure                                 -> LONG_TERM
      4. an ACTIVITY marker                          -> SCRATCH if episodic, else WORKING
      5. otherwise                                   -> LONG_TERM
    """
    raise NotImplementedError("implement promotion_tier")


def would_promote(memories: list[Memory], turns: dict[str, str]) -> dict[Tier, list[Memory]]:
    out: dict[Tier, list[Memory]] = {t: [] for t in Tier}
    for m in memories:
        out[promotion_tier(m, turns.get(m.provenance.source_id, ""))].append(m)
    return out


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.fixtures import load_turns
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-promote.jsonl")
    store.clear()
    ingest(store, scope)
    memories = store.all()

    turns = {f"s{t['session']}:{t['ts']}": t["text"] for t in load_turns(user_only=True)}
    tiers = would_promote(memories, turns)

    print(f"current system promotes {len(memories)} of {len(memories)}\n")
    print("with a promotion gate:")
    for tier, group in tiers.items():
        if group:
            print(f"  {tier.value:<10} {len(group):>3}")

    print("\ndemoted:")
    for tier in (Tier.SCRATCH, Tier.WORKING):
        for m in tiers[tier]:
            print(f"  {tier.value:<10} {m.content[:62]}")


if __name__ == "__main__":
    main()
