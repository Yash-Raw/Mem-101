"""Lab: written is not the same as reachable.

    uv run python curriculum/intermediate/extraction-quality/lab/lab.py
"""
from __future__ import annotations

from memlab.eval.extraction import NATURAL_QUERY, REQUIRED_STATES, ExtractionScore
from memlab.extract.gate import passes
from memlab.retrieve.embedding import EmbeddingRetriever
from memlab.types import Memory, MemoryType, Scope


def score(
    memories: list[Memory],
    turns: dict[str, str] | None = None,
    scope: Scope | None = None,
    k: int = 10,
) -> ExtractionScore:
    """TODO: return an ExtractionScore with three measurements.

      state_recall  -- of REQUIRED_STATES, how many exist as a live SEMANTIC
                       memory. An episode does not count.
      reachability  -- of those, how many surface within top-k for
                       NATURAL_QUERY[name]. Use live_only=True.
      over_extracted -- contents the durability gate would drop; pass the
                       originating turn text so explicit markers are honoured.

    Record the per-state rank in `reached` too -- the ranks are more
    instructive than the ratio.
    """
    raise NotImplementedError("implement score")


def score_profiles(k: int = 10) -> dict[str, ExtractionScore]:
    from memlab.app.chat import ingest
    from memlab.fixtures import load_turns
    from memlab.pipeline import at, get
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    turns = {f"s{t['session']}:{t['ts']}": t["text"] for t in load_turns(user_only=True)}
    out = {}
    for name in ("beginner", "intermediate"):
        store = JsonlStore(f"/tmp/memlab-quality-{name}.jsonl")
        store.clear()
        ingest(store, scope, get(name) if name == "beginner" else at("I1"))
        out[name] = score(store.all(), turns, scope, k=k)
    return out


def main() -> None:
    scores = score_profiles()
    print(f"{'':<16}{'written':>9}{'reach@10':>10}{'over-extr':>11}   n")
    for name, s in scores.items():
        print(f"{name:<16}{s.state_recall:>8.0%}{s.reachability:>10.0%}"
              f"{s.over_extraction_rate:>11.0%}{s.total:>4}")

    print("\nper-state rank for the question it exists to answer:")
    for name, s in scores.items():
        print(f"  {name}")
        for state, rank in s.reached.items():
            written = "written" if s.found[state] else "ABSENT "
            print(f"    {state:<16} {written}  rank {rank}")

    dropped = scores["beginner"].over_extracted
    print(f"\nbeginner would drop {len(dropped)} records under the gate:")
    for c in dropped:
        print(f"  - {c}")


if __name__ == "__main__":
    main()
