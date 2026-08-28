"""Three questions, one interface, and three places that assumed now."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from memlab import labkit
from memlab.app.chat import ask, ingest
from memlab.pipeline import at
from memlab.retrieve.scoped import search as scoped_search
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Question = _solution.Question
answer = _solution.answer
classify = _solution.classify
eligible = _solution.eligible
parse_when = _solution.parse_when
temporal_search = _solution.temporal_search

PRIYA = Scope(user="priya")
NOW = datetime(2026, 8, 27, tzinfo=UTC)
CASES = [
    ("where did I work in June 2025?", "data engineer at Northwind"),
    ("what did I drink in 2025?", "does not drink coffee"),
    ("where did Priya live in 2025?", "47 Halloway"),
    ("how did I like answers in 2025?", "prefers detailed explanations"),
]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    p = at("A1")
    s = JsonlStore(tmp_path_factory.mktemp("tq") / "m.jsonl")
    ingest(s, PRIYA, p)
    p.vectors.index(s.all())
    return s, p


def _rank1(hits, want):
    return next(
        (i + 1 for i, h in enumerate(hits) if want in h.memory.content), None
    ) == 1


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.classify("where do I work?")


@pytest.mark.parametrize(
    "text,expected",
    [
        ("where do I work?", Question.NOW),
        ("what should I not eat?", Question.NOW),
        ("where did I work in June 2025?", Question.THEN),
        ("when did I change jobs?", Question.CHANGED),
        ("how long was I at Northwind?", Question.CHANGED),
    ],
)
def test_routing(text, expected) -> None:
    assert classify(text).question is expected


def test_a_named_time_is_an_interval(built) -> None:
    """"In 2025" collapsed to an instant asks about January 1st."""
    assert parse_when("where did I work in June 2025?") == (
        datetime(2025, 6, 1, tzinfo=UTC),
        datetime(2025, 7, 1, tzinfo=UTC),
    )
    assert parse_when("what did I drink in 2025?") == (
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert parse_when("where do I work?") is None


def test_the_level_two_read_path_finds_none_of_them(built) -> None:
    """Not ranked low -- absent. Similarity has no opinion about time."""
    store, pipeline = built
    for q, want in CASES:
        hits = ask(store, PRIYA, q, k=5, pipeline=pipeline)[1]
        assert not any(want in h.memory.content for h in hits), q


def test_the_staged_release(built) -> None:
    """0 -> 0 -> 1 -> 4. Neither filter alone gets there."""
    store, pipeline = built
    memories = store.all()

    def score(**kwargs):
        return sum(
            _rank1(
                scoped_search(
                    q, eligible(q, memories, NOW), PRIYA,
                    k=5, index=pipeline.vectors, **kwargs,
                ),
                w,
            )
            for q, w in CASES
        )

    assert score() == 0
    assert score(live_only=False) == 1
    assert score(live_only=False, retrievable_only=False) == 4


def test_the_tier_cap_is_the_second_now_assumption(built) -> None:
    """Demoted for being stale, which is what makes it the answer."""
    store, _ = built
    m = next(x for x in store.all() if "data engineer at Northwind" in x.content)
    assert m.tier.value == "working"
    assert not m.is_live


def test_one_call_answers_both_questions(built) -> None:
    store, pipeline = built
    ms = store.all()
    then = temporal_search(
        "where did I work in June 2025?", ms, PRIYA, k=1, index=pipeline.vectors, now=NOW
    )
    now = temporal_search(
        "where do I work?", ms, PRIYA, k=1, index=pipeline.vectors, now=NOW
    )
    assert "Northwind Labs" in then[0].memory.content
    assert "Calico Systems" in now[0].memory.content


def test_the_filter_alone_is_correct_and_unusable(built) -> None:
    """Eligibility is not relevance -- the I5 mistake, in a new place."""
    ms = built[0].all()
    assert len(eligible("where do I work?", ms, NOW)) == 30
    assert len(answer("when did I change jobs?", ms, NOW)) == 88


def test_changed_keeps_the_axis_on_each_event(built) -> None:
    """A changelog flattened to memories is a history rendered as facts."""
    events = answer("when did I change jobs?", built[0].all(), NOW)
    axes = {axis for _m, axis in events}
    assert axes == {"became true", "stopped being true", "believed", "retired"}
    employer = [
        (m, a) for m, a in events if "Northwind" in m.content or "Calico" in m.content
    ]
    assert len(employer) == 12
