"""Lab: what not forgetting costs per query.

    uv run python curriculum/intermediate/why-forgetting-is-a-feature/lab/lab.py
"""
from __future__ import annotations

from memlab.forget.audit import ANSWER_MARKERS, BudgetAudit, tier_census  # noqa: F401
from memlab.types import Memory


def audit_context(hits: list, k: int, store: list[Memory]) -> BudgetAudit:
    """TODO: how many of the k slots carried a claim the answer needed?

    A slot is useful if its content contains an ANSWER_MARKER. Everything else
    is a slot a useful memory did not get.
    """
    raise NotImplementedError("implement audit_context")


def projected_growth(store: list[Memory], sessions: int, horizon: int) -> tuple[int, int]:
    """TODO: (today, at horizon) at the rate this corpus actually produced."""
    raise NotImplementedError("implement projected_growth")


def main() -> None:
    from memlab.app.chat import ask, ingest
    from memlab.eval.exam import QUESTION
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    for name in ("I4", "I5"):
        pipeline = at(name)
        store = JsonlStore(f"/tmp/memlab-audit-{name}.jsonl")
        store.clear()
        ingest(store, scope, pipeline)
        _, hits = ask(store, scope, QUESTION, k=5, pipeline=pipeline)

        audit = audit_context(hits, 5, store.all())
        print(f"@{name}: {audit.useful} of {audit.slots} slots useful, "
              f"{audit.waste:.0%} wasted   tiers={tier_census(store.all())}")
        for content in audit.wasted_contents:
            print(f"        wasted: {content[:58]}")
        print()

    store = JsonlStore("/tmp/memlab-audit-I5.jsonl")
    today, later = projected_growth(store.all(), 13, 130)
    print(f"growth at this corpus's rate: {today} memories from 13 sessions "
          f"-> {later} at 130. The budget is still five slots.")


if __name__ == "__main__":
    main()
