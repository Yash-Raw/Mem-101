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


def test_the_worst_one_was_off_by_249_days(built) -> None:
    """The size of the error is the argument. A fact about 2025 dated 2026.

    Measured against the write clock, which A1's parser deliberately leaves
    alone -- `happened_at` still means "when this was asserted". So this stays
    a live assertion after the flip rather than becoming a permanent skip.
    """
    store, _ = built["advanced"]
    m = next(x for x in store.all() if "before the move" in x.content)
    assert (m.happened_at - datetime(2025, 8, 2, tzinfo=UTC)).days == 249


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


# --- A2 target: consolidation runs once, because the corpus arrives at once --
def _walk(pipeline, consolidate_every_turn: bool, tmp_path):
    """Replay the corpus turn by turn, the way a live system receives it."""
    from memlab.app.chat import _agent_memories
    from memlab.fixtures import load_turns

    store = JsonlStore(tmp_path / f"walk-{consolidate_every_turn}.jsonl")
    store.clear()
    runs, divergent = 0, []
    reference = JsonlStore(tmp_path / f"ref-{consolidate_every_turn}.jsonl")
    reference.clear()

    turns = [t for t in load_turns(user_only=True) if t["session"] < 14]
    for n, turn in enumerate(turns, 1):
        for st, eager in ((store, consolidate_every_turn), (reference, True)):
            memories = pipeline.extract(turn, PRIYA)
            if pipeline.resolve is not None:
                memories = pipeline.resolve(memories, st.all())
            st.add(memories)
            if eager and pipeline.consolidate is not None:
                st.replace(pipeline.consolidate(st.all()))
                if st is store:
                    runs += 1
        if _stale(store) != _stale(reference):
            divergent.append(n)

    store.add(_agent_memories(PRIYA))
    if pipeline.consolidate is not None:
        store.replace(pipeline.consolidate(store.all()))
        runs += 1
    return store, runs, divergent, len(turns)


def _stale(store) -> int:
    return sum(
        1 for m in store.all() if m.is_live and "data engineer at Northwind" in m.content
    )


def test_deferring_consolidation_leaves_the_store_wrong_for_eleven_turns(
    tmp_path,
) -> None:
    """46% of the conversation believing a job she had already left.

    The shipped `ingest()` consolidates once, at the end -- which is only
    possible because the corpus arrives all at once. A live system receives
    one turn at a time and has to choose: pay per turn, or be wrong in
    between. The window is the cost, not the compute.
    """
    pipeline = get("advanced")
    _store, runs, divergent, total = _walk(pipeline, False, tmp_path)
    assert runs == 1, "one consolidation, at the end of the batch"
    assert (len(divergent), total) == (11, 24)
    assert (divergent[0], divergent[-1]) == (14, 24)


def test_but_it_converges_to_the_same_store(tmp_path) -> None:
    """Order-independent, measured. This is what makes deferral safe at all."""
    pipeline = get("advanced")
    deferred, _r, _d, _t = _walk(pipeline, False, tmp_path)
    eager, runs, _d2, _t2 = _walk(pipeline, True, tmp_path)
    assert runs == 25
    assert {m.id for m in deferred.all()} == {m.id for m in eager.all()}
    live = sum(m.is_live for m in deferred.all())
    assert live == sum(m.is_live for m in eager.all()) == 30, (
        "and on the same live set as the shipped batch ingest"
    )


# --- A3 target: an unauthorised write does damage without being believed ----
def _with_agent_write(tmp_path, tag, when=None, content="Priya works at Meridian Health"):
    """Ingest with one extra agent-written memory, through the real path."""
    from memlab.app import chat
    from memlab.types import Memory, MemoryType, Provenance

    original = chat._agent_memories
    if when is not None:
        def patched(scope):
            return [
                *original(scope),
                Memory(
                    content=content,
                    type=MemoryType.SEMANTIC,
                    # The user's own namespace, not the agent's. Nothing checks.
                    scope=Scope(user=scope.user),
                    happened_at=when,
                    provenance=Provenance(
                        source_id="travel-agent:z",
                        speaker="travel-agent",
                        authority=0.3,
                    ),
                    confidence=0.3,
                ),
            ]
        chat._agent_memories = patched
    try:
        pipeline = get("advanced")
        store = JsonlStore(tmp_path / f"{tag}.jsonl")
        store.clear()
        ingest(store, PRIYA, pipeline)
        if pipeline.vectors is not None:
            pipeline.vectors.index(store.all())
        return store, pipeline
    finally:
        chat._agent_memories = original


def _eligible_count(store):
    from memlab.retrieve.scoped import eligible

    return len(eligible(store.all(), PRIYA))


def test_a_low_trust_agent_can_write_into_the_users_own_namespace(tmp_path) -> None:
    """Read isolation is enforced; write authorisation does not exist."""
    from memlab.store.scopes import leak_check, visible

    store, _p = _with_agent_write(tmp_path, "rogue", datetime(2026, 5, 1, tzinfo=UTC))
    rogue = next(m for m in store.all() if "Meridian" in m.content)
    assert rogue.scope.agent is None, "filed as though the user had said it"
    assert any(m.id == rogue.id for m in visible(store.all(), PRIYA))
    assert not any(m.id == rogue.id for m in leak_check(store.all(), PRIYA)), (
        "leak_check catches cross-USER reads; this is not one"
    )


def test_a_future_dated_write_re_ages_the_whole_store(tmp_path) -> None:
    """The claim is never believed. Its timestamp does the damage.

    `forget.decay.reference_now` is the newest event in the store, so one
    record dated ahead ages everything else past the LONG_TERM threshold --
    before arbitration has looked at the claim at all.
    """
    from memlab.app.chat import ask

    clean, clean_pipe = _with_agent_write(tmp_path, "clean")
    inside, _ = _with_agent_write(tmp_path, "inside", datetime(2026, 5, 1, tzinfo=UTC))
    ahead, ahead_pipe = _with_agent_write(
        tmp_path, "ahead", datetime(2027, 5, 16, tzinfo=UTC)
    )

    assert (len(clean.all()), _eligible_count(clean)) == (37, 18)
    assert (len(inside.all()), _eligible_count(inside)) == (38, 18)
    assert (len(ahead.all()), _eligible_count(ahead)) == (38, 5)

    def top2(store, pipeline):
        return [h.memory.content for h in ask(store, PRIYA, "where do I work?",
                                              k=2, pipeline=pipeline)[1]]

    assert "Calico Systems" in top2(clean, clean_pipe)[0]
    assert not any("Calico" in c for c in top2(ahead, ahead_pipe)), (
        "the employer fact is no longer retrievable"
    )


# --- A4 target: there is no user model, and the naive one is wrong ----------
def test_the_naive_user_model_is_mostly_not_about_the_user(built) -> None:
    from memlab.evolve.conflict import slot_of
    from memlab.types import MemoryType

    store, _ = built["advanced"]
    naive = [
        m for m in store.all() if m.type is MemoryType.SEMANTIC and m.is_live
    ]
    assert len(naive) == 19
    third_party = [m for m in naive if m.entities]
    assert len(third_party) == 2, "Samira's job, in a model of Priya"
    assert sum(1 for m in naive if not slot_of(m)) == 6, "no attribute to key on"


# --- A5 target: the procedure is stored, live, and unreachable --------------
def test_the_procedure_is_never_retrieved(built) -> None:
    """gold predicts the steps come back shuffled. They do not come back."""
    from memlab.app.chat import ask
    from memlab.types import MemoryType

    store, pipeline = built["advanced"]
    if pipeline.vectors is not None:
        pipeline.vectors.index(store.all())
    procedures = [m for m in store.all() if m.type is MemoryType.PROCEDURAL]
    assert len(procedures) == 2
    assert all(m.is_live for m in procedures)

    hits = ask(store, PRIYA, "how do I do the weekly report?", k=5, pipeline=pipeline)[1]
    assert not any(h.memory.type is MemoryType.PROCEDURAL for h in hits), (
        "not ranked low -- absent"
    )

    hits = ask(store, PRIYA, "what are the steps for the weekly report",
               k=5, pipeline=pipeline)[1]
    assert hits[0].memory.type is MemoryType.PROCEDURAL
    assert "diff step matters most" in hits[0].memory.content, (
        "and it is the commentary, not the recipe"
    )
