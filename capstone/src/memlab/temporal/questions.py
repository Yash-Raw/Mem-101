"""Three questions that look alike and route differently.

    NOW      "where do I work?"                 event axis, open interval
    THEN     "where did I work in June 2025?"   event axis, pinned
    CHANGED  "when did I change jobs?"          both axes, as a changelog

The read path built through Level 2 answers exactly one of them, and answers
the other two with it. That is not a ranking failure: similarity has no
opinion about time, so a question with a date in it retrieves the same
memories as a question without one, and the date is spent as vocabulary.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from ..types import Memory
from .validity import as_of, changed_between, overlapping


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
    if _CHANGED.search(text):
        return Routed(Question.CHANGED)
    when = parse_when(text)
    if when is not None:
        return Routed(Question.THEN, when)
    if _PAST.search(text):
        return Routed(Question.THEN)  # past tense, no date -- ambiguous on purpose
    return Routed(Question.NOW)


def parse_when(text: str) -> tuple[datetime, datetime] | None:
    """The span a question names, at the precision it named it."""
    year = _YEAR.search(text)
    if not year:
        return None
    y = int(year.group())
    month = _MONTH.search(text)
    if month:
        m = _MONTHS[month.group()[:3].lower()]
        start = datetime(y, m, 1, tzinfo=UTC)
        end = datetime(y + 1, 1, 1, tzinfo=UTC) if m == 12 else datetime(y, m + 1, 1, tzinfo=UTC)
        return start, end
    return datetime(y, 1, 1, tzinfo=UTC), datetime(y + 1, 1, 1, tzinfo=UTC)


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
    from ..retrieve.scoped import search

    routed = classify(text)
    pool = eligible(text, memories, now)
    if routed.question is Question.NOW:
        return search(text, pool, scope, k=k, index=index)
    return search(
        text, pool, scope, k=k, index=index, live_only=False, retrievable_only=False
    )


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
