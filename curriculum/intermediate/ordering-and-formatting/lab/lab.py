"""Lab: what the line format costs.

    uv run python curriculum/intermediate/ordering-and-formatting/lab/lab.py
"""

from __future__ import annotations

from memlab.retrieve.embedding import Hit

DATED = "dated"
YEAR = "year"
BARE = "bare"


def render(hit: Hit, precision: str = DATED) -> str:
    """TODO: one memory, one line, at DATED / YEAR / BARE precision.

    Never truncated -- half a fact is a hazard. A memory with no happened_at
    renders bare whatever the precision asks for.
    """
    raise NotImplementedError("implement render")


def order(hits: list[Hit]) -> list[Hit]:
    """Score order, not chronological.

    Attention degrades over long spans, so the most relevant memory belongs
    first. Chronological ordering reads more naturally and buries the best
    answer in the middle, which is the one place it is least likely to be used.
    """
    return sorted(hits, key=lambda h: -h.score)


def main() -> None:
    from memlab.app.chat import ask, ingest
    from memlab.assemble.simple import HEADER, estimate_tokens
    from memlab.assemble.value import COMPACT_HEADER
    from memlab.eval.exam import QUESTION
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    NEEDED = ("works at Calico", "does not eat meat", "eats fish", "gluten")
    scope = Scope(user="priya")
    pipeline = at("I7")
    store = JsonlStore("/tmp/memlab-ordering.jsonl")
    store.clear()
    ingest(store, scope, pipeline)
    pipeline.vectors.index(store.all())
    _ctx, hits = ask(store, scope, QUESTION, k=5, pipeline=pipeline)
    needed = [h for h in hits if any(n in h.memory.content for n in NEEDED)]

    print(f"{'precision':<10}{'example':<44}{'4 facts':>9}{'+full':>7}{'+compact':>10}")
    for precision in (DATED, YEAR, BARE):
        facts = sum(estimate_tokens(render(h, precision)) for h in needed)
        example = render(needed[0], precision)
        print(f"{precision:<10}{example[:42]:<44}{facts:>9}"
              f"{facts + estimate_tokens(HEADER):>7}{facts + estimate_tokens(COMPACT_HEADER):>10}")

    print("\nscore order vs chronological:")
    by_score = order(hits)
    by_time = sorted(hits, key=lambda h: h.memory.happened_at)
    for i, (s, c) in enumerate(zip(by_score, by_time), 1):
        mark = "  <-- same" if s.memory.id == c.memory.id else ""
        print(f"   {i}. {s.memory.content[:30]:<32}| {c.memory.content[:30]}{mark}")
    agree = sum(s.memory.id == c.memory.id for s, c in zip(by_score, by_time))
    print(f"\n   {agree} of {len(hits)} positions agree -- on THIS corpus the two")
    print("   orderings coincide. The argument for score order still holds;")
    print("   this data simply cannot distinguish them.")


if __name__ == "__main__":
    main()
