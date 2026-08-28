"""Lab: three questions that look alike and route differently.

    uv run python curriculum/advanced/temporal-questions/lab/lab.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from memlab.temporal.validity import as_of, changed_between, overlapping
from memlab.types import Memory


class Question(Enum):
    NOW = "now"
    THEN = "then"
    CHANGED = "changed"


# Deliberately small and deliberately explicit. A classifier that guesses is
# worse than one that abstains: routing "when did I change jobs" to NOW
# returns a confident current answer to a question about history.
_CHANGED = re.compile(
    r"\bwhen did\b|\bwhen d[oi]|\bhow long\b|\bsince when\b|\bchanged?\b|\bused to\b",
    re.IGNORECASE,
)
_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_MONTH = re.compile(
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b", re.IGNORECASE
)
_PAST = re.compile(r"\bdid\b|\bwas\b|\bwere\b|\bback then\b|\bat the time\b", re.IGNORECASE)

_MONTHS = {
    m: i + 1
    for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    )
}


@dataclass(frozen=True)
class Routed:
    """Where the question routes, and the interval it named.

    `when` is a half-open span, not an instant, because that is how questions
    are actually asked. "In June 2025" is a month; "in 2025" is a year. A
    parser that collapses both to a timestamp answers about the 1st.
    """

    question: Question
    when: tuple[datetime, datetime] | None = None


def classify(text: str) -> Routed:
    """Which of the three is being asked, and about when."""
    raise NotImplementedError("implement classify")


def parse_when(text: str) -> tuple[datetime, datetime] | None:
    """The span a question names, at the precision it named it."""
    raise NotImplementedError("implement parse_when")


def answer(
    text: str, memories: list[Memory], now: datetime | None = None
) -> list[Memory] | list[tuple[Memory, str]]:
    """Route, then apply the temporal filter the route asks for.

    Returns memories for NOW and THEN, and (memory, axis) pairs for CHANGED --
    different shapes because they are different questions. Flattening them to
    one shape is how a changelog gets rendered as a list of current facts.
    """
    now = now or datetime.now(UTC)
    routed = classify(text)
    if routed.question is Question.NOW:
        return as_of(memories, now)
    if routed.question is Question.THEN:
        if routed.when is None:
            return as_of(memories, now)
        return overlapping(memories, *routed.when)
    start = min((m.recorded_at for m in memories), default=now)
    return changed_between(memories, start, now)


def temporal_search(
    text: str, memories: list[Memory], scope, k: int = 5, index=None, now=None
):
    """Filter on the event axis, then rank -- with the present unpinned.

    Both of the read path's hard filters have their clock set to now, and
    both are right for every question Level 2 asks. A question about the past
    has to release both: `live_only` because the answer is a retired belief,
    and `retrievable_only` because the I5 tier cap demoted it for being stale,
    which is the property that makes it the answer.
    """

    raise NotImplementedError("implement temporal_search")


def eligible(
    text: str, memories: list[Memory], now: datetime | None = None
) -> list[Memory]:
    """The temporal filter alone: which memories the question can be about.

    This is a *filter*, not an answer. On this corpus "where do I work?"
    leaves 30 memories eligible -- correct, and useless as a reply. Eligibility
    and relevance are different axes, exactly as salience and relevance were
    in I5, and the composition is filter-then-rank.
    """
    routed = classify(text)
    if routed.question is Question.CHANGED:
        return [m for m, _axis in answer(text, memories, now)]
    out = answer(text, memories, now)
    return [m for m in out if isinstance(m, Memory)]


NOW_T = datetime(2026, 8, 27, tzinfo=UTC)
CASES = [
    ("where did I work in June 2025?", "data engineer at Northwind"),
    ("what did I drink in 2025?", "does not drink coffee"),
    ("where did Priya live in 2025?", "47 Halloway"),
    ("how did I like answers in 2025?", "prefers detailed explanations"),
]
ROUTING = [
    "where do I work?",
    "where did I work in June 2025?",
    "when did I change jobs?",
    "what should I not eat?",
    "how long was I at Northwind?",
]


def _rank1(hits, want):
    return next((i + 1 for i, h in enumerate(hits) if want in h.memory.content), None) == 1


def main() -> None:
    from memlab.app.chat import ask, ingest
    from memlab.pipeline import at
    from memlab.retrieve.scoped import search as scoped_search
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    pipeline = at("A1")
    store = JsonlStore("/tmp/memlab-questions.jsonl")
    store.clear()
    ingest(store, scope, pipeline)
    pipeline.vectors.index(store.all())
    memories = store.all()

    print("routing:\n")
    for q in ROUTING:
        r = classify(q)
        span = f"{r.when[0].date()} .. {r.when[1].date()}" if r.when else ""
        print(f"   {q:36} -> {r.question.value:8} {span}")

    print("\n   the memory that was true then, at rank 1:\n")
    baseline = sum(
        _rank1(ask(store, scope, q, k=5, pipeline=pipeline)[1], w) for q, w in CASES
    )
    print(f"   {'Level 2 read path, unchanged':44}{baseline} of {len(CASES)}")

    stages = [
        ("+ temporal filter, nothing released", {}),
        ("+ live_only released", {"live_only": False}),
        ("+ retrievable_only released too",
         {"live_only": False, "retrievable_only": False}),
    ]
    for label, kwargs in stages:
        n = sum(
            _rank1(
                scoped_search(
                    q, eligible(q, memories, NOW_T), scope,
                    k=5, index=pipeline.vectors, **kwargs,
                ),
                w,
            )
            for q, w in CASES
        )
        print(f"   {label:44}{n} of {len(CASES)}")

    print("\n   and the same call answers both:\n")
    for q in ("where did I work in June 2025?", "where do I work?"):
        top = temporal_search(q, memories, scope, k=1, index=pipeline.vectors, now=NOW_T)
        print(f"   {q:36} -> {top[0].memory.content}")

    print("\n   the filter used alone:\n")
    print(f"   'where do I work?'       leaves "
          f"{len(eligible('where do I work?', memories, NOW_T))} memories eligible")
    print(f"   'when did I change jobs?' produces "
          f"{len(answer('when did I change jobs?', memories, NOW_T))} change events")


if __name__ == "__main__":
    main()
