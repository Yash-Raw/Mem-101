"""Level 3's targets, red until the module that fixes each one lands.

Same discipline as test_v1_failures.py: assert what is true *now*, gate the
expectation on a pipeline capability, and let the module that switches that
capability on flip its own test. A target that is xfail-ed says "we know";
a target that asserts the broken behaviour says what is broken, in numbers.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from memlab.app.chat import ingest
from memlab.pipeline import at, get
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

PRIYA = Scope(user="priya")

# gold.yml, relative_time: the phrase, and the date it actually refers to.
ANCHORS = [
    ("used to cycle to work before the move", datetime(2025, 8, 2, tzinfo=UTC)),
    ("left Northwind Labs last month", datetime(2025, 12, 1, tzinfo=UTC)),
    ("diagnosed with a gluten intolerance last week", datetime(2026, 5, 8, tzinfo=UTC)),
]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = {}
    for name in ("intermediate", "advanced"):
        p = get(name)
        s = JsonlStore(tmp_path_factory.mktemp(name) / "m.jsonl")
        ingest(s, PRIYA, p)
        out[name] = (s, p)
    return out


@pytest.fixture(scope="module")
def turn_timestamps():
    """Every instant anything was written at -- agent writes included.

    Counting only user turns makes the three calendar-agent memories look
    like they carry a distinct event time. They do not; the agent stamps its
    own clock exactly as the extractor does.
    """
    from memlab.temporal.clocks import turn_timestamps as ts

    return ts()


# --- A1 target 1: the second clock is a copy of the first -------------------
@pytest.mark.parametrize("name", ["intermediate", "advanced"])
def test_event_time_is_mostly_just_ingestion_time(built, turn_timestamps, name) -> None:
    """37 of 37. Two clocks in the record, and neither reads the sentence."""
    store, pipeline = built[name]
    from memlab.temporal.clocks import event_start

    memories = store.all()
    copied = sum(
        1
        for m in memories
        if event_start(m) and event_start(m).isoformat()[:19] in turn_timestamps
    )
    if pipeline.anchor is None:
        assert (copied, len(memories)) == (37, 37)
        if not pipeline.bitemporal:
            assert not any(m.valid_to for m in memories), "and no fact has an end"
    else:
        assert copied < 37, "anchoring moved at least one event time off the write clock"


@pytest.mark.parametrize("fragment,truth", ANCHORS)
@pytest.mark.parametrize("name", ["intermediate", "advanced"])
def test_relative_phrases_are_not_resolved(built, name, fragment, truth) -> None:
    """`before the move` is stored as though it happened on the day she said it."""
    store, pipeline = built[name]
    from memlab.temporal.clocks import event_start

    m = next(x for x in store.all() if fragment in x.content)
    off_by = abs((event_start(m) - truth).days)
    if pipeline.anchor is None:
        assert off_by > 0, "the phrase was never parsed, so this cannot be right"
    else:
        assert off_by <= 1, f"{fragment!r} anchors to {truth.date()}"


def test_the_worst_one_is_off_by_249_days(built) -> None:
    """The size of the error is the argument. A fact about 2025 dated 2026."""
    store, pipeline = built["advanced"]
    if pipeline.anchor is not None:
        pytest.skip("A1 has landed; the anchored assertion above covers this")
    from memlab.temporal.clocks import event_start

    m = next(x for x in store.all() if "before the move" in x.content)
    assert (event_start(m) - datetime(2025, 8, 2, tzinfo=UTC)).days == 249


# --- A1 target 2: as-of queries are not expressible -------------------------
AS_OF = datetime(2025, 6, 1, tzinfo=UTC)


def test_a_question_about_the_past_is_answered_with_the_future(built) -> None:
    """"What did you believe about my employer in June 2025?"

    Every answer the live read path can offer is about Calico -- a job she had
    not been offered yet. `live_only` is a filter on *belief* time, applied to
    a question about *event* time.
    """
    store, _ = built["advanced"]
    employer = [m for m in store.live() if "Calico" in m.content or "Northwind" in m.content]
    assert len(employer) == 4
    assert all(m.happened_at > AS_OF for m in employer), (
        "not one of them was true on the date asked about"
    )


def test_and_narrowing_by_event_time_returns_nothing(built) -> None:
    """The obvious fix returns an empty answer, which is worse than a wrong one.

    The memory that *is* correct for June 2025 is in the store and carries both
    timestamps needed to prove it -- happened_at 2025-03-04, retired
    2025-12-08. The data is sufficient. The query is not expressible.
    """
    store, pipeline = built["advanced"]
    from memlab.temporal.clocks import event_start

    narrowed = [
        m
        for m in store.live()
        if event_start(m) <= AS_OF and ("Calico" in m.content or "Northwind" in m.content)
    ]
    if pipeline.anchor is None:
        assert narrowed == []

    answer = next(m for m in store.all() if "data engineer at Northwind" in m.content)
    assert answer.happened_at < AS_OF < answer.invalid_at, (
        "true then, retired later -- both facts recorded, neither reachable"
    )


def test_advanced_starts_as_intermediate_plus_nothing(built) -> None:
    """Until A1 lands, `advanced` is Level 2. Every @I* figure must be safe."""
    inter, adv = built["intermediate"][0], built["advanced"][0]
    assert [m.id for m in inter.all()] == [m.id for m in adv.all()]
    assert at("A1").name == "advanced@A1"
