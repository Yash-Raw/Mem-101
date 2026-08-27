"""Lab: the candidate set is the bigger lever.

    uv run python curriculum/intermediate/scope-then-rank/lab/lab.py
"""
from __future__ import annotations

from memlab.llm.fake import cosine, embed_text
from memlab.types import Memory, Scope, Tier


def eligible(memories: list[Memory], scope: Scope, retrievable_only: bool = True) -> list[Memory]:
    """TODO: three hard filters, before anything is scored.

      scope     m.scope.matches(scope)        (I2)
      validity  m.is_live                     (I4)
      tier      m.tier is Tier.LONG_TERM      (I5)

    Guard the tier filter: if NOTHING in the pool is long_term -- the beginner
    profile, which never assigned tiers -- skip it rather than returning an
    empty result.
    """
    raise NotImplementedError("implement eligible")


def rank_only(query: str, pool: list[Memory]) -> list[tuple[float, Memory]]:
    q = embed_text(query)
    scored = [(cosine(q, embed_text(m.content)), m) for m in pool]
    scored.sort(key=lambda p: -p[0])
    return scored


def rank_then_filter(
    query: str, memories: list[Memory], scope: Scope, k: int = 5
) -> list[Memory]:
    """The wrong order. Returns fewer than k, unpredictably."""
    ranked = rank_only(query, [m for m in memories if m.scope.matches(scope)])
    top = [m for _, m in ranked[:k]]
    return [m for m in top if m.is_live and m.tier is Tier.LONG_TERM]


def employer_rank(query: str, pool: list[Memory]) -> int | None:
    return next(
        (i for i, (_, m) in enumerate(rank_only(query, pool), 1)
         if "works at Calico" in m.content),
        None,
    )


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.eval.exam import QUESTION
    from memlab.pipeline import at, get
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-scoped.jsonl")
    store.clear()
    ingest(store, scope, at("I5"))
    memories = store.all()

    live = [m for m in memories if m.is_live]
    filtered = eligible(memories, scope)
    print(f"live only            pool={len(live):>2}  employer rank={employer_rank(QUESTION, live)}")
    print(f"live + LONG_TERM     pool={len(filtered):>2}  employer rank={employer_rank(QUESTION, filtered)}\n")

    print("top-5 after filtering:")
    for _score, m in rank_only(QUESTION, filtered)[:5]:
        print(f"   {m.content[:54]}")

    wrong = rank_then_filter(QUESTION, memories, scope, k=5)
    print(f"\nrank-then-filter returns {len(wrong)} results for k=5 -- fewer than asked,")
    print("and how many depends on how much retired material sits near the query.")

    beginner_store = JsonlStore("/tmp/memlab-scoped-b.jsonl")
    beginner_store.clear()
    ingest(beginner_store, scope, get("beginner"))
    print(f"\nbeginner profile (no tiers): eligible returns "
          f"{len(eligible(beginner_store.all(), scope))} of {len(beginner_store.all())} -- "
          "the guard failing open")


if __name__ == "__main__":
    main()
