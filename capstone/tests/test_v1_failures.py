"""The seven failures, measured against every profile.

This file is the course's regression spine. Each failure is asserted twice: it
MUST still be present under `beginner`, and it must be fixed under a profile
whose pipeline has the stage that fixes it.

Expectations are derived from the pipeline's own capabilities rather than
hardcoded per level -- `entity fragmentation` is expected fixed exactly when
`pipeline.resolve` is wired up, `staleness` exactly when `pipeline.live_only`
is on. So a lesson that switches on a stage flips its test automatically, and
the suite stays green after every commit instead of going red for a whole
module. It also means a stage that claims a fix and does not deliver one fails
immediately, in the lesson that claimed it.

Numbers pinned here are quoted verbatim in the Beginner lessons. If one moves,
that is a build break, not a number to update.
"""
from __future__ import annotations

import pytest
from memlab.app.chat import ingest
from memlab.eval.exam import QUESTION, exam_answer
from memlab.pipeline import get
from memlab.retrieve.embedding import EmbeddingRetriever
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

PRIYA = Scope(user="priya")
PROFILES = ["beginner", "intermediate"]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """Every profile, ingested once."""
    out = {}
    for name in PROFILES:
        pipeline = get(name)
        store = JsonlStore(tmp_path_factory.mktemp(name) / "memories.jsonl")
        ingest(store, PRIYA, pipeline)
        out[name] = (store, pipeline)
    return out


def ranked(store):
    memories = store.all()
    return EmbeddingRetriever().search(QUESTION, memories, PRIYA, k=len(memories))


def rank_of(hits, needle: str) -> int | None:
    return next((i for i, h in enumerate(hits, 1) if needle in h.memory.content), None)


def live_semantic(store, *markers: str):
    return [
        m for m in store.all()
        if m.is_live and m.type is MemoryType.SEMANTIC
        and any(k in m.content for k in markers)
    ]


# --- the baseline still works -----------------------------------------------
def test_the_loop_closes(built) -> None:
    store, _ = built["beginner"]
    assert len(store.all()) == 36
    assert {m.type for m in store.all()} == {
        MemoryType.SEMANTIC, MemoryType.EPISODIC, MemoryType.PROCEDURAL
    }


def test_it_survives_restart(built) -> None:
    store, _ = built["beginner"]
    assert len(JsonlStore(store.path).all()) == 36


def test_beginner_ranks_are_unmoved(built) -> None:
    """The twelve figures quoted across Beginner. A tripwire, not a test of merit."""
    hits = ranked(built["beginner"][0])
    assert rank_of(hits, "at Northwind Labs") == 9
    assert rank_of(hits, "at Calico now") == 35
    assert rank_of(hits, "completed her first week") == 6


# --- failure 1 & 2: staleness and accumulating contradictions ---------------
# fixed by supersession (I4), detected via pipeline.live_only
@pytest.mark.parametrize("profile", PROFILES)
def test_staleness(built, profile) -> None:
    store, pipeline = built[profile]
    employers = live_semantic(store, "Northwind", "Calico")

    if not pipeline.live_only:
        assert len(employers) >= 2, "both employers live, nothing retired"
        assert all(m.superseded_by is None for m in store.all())
    else:
        assert len(employers) == 1 and "Calico" in employers[0].content
        retired = [m for m in store.all() if "Northwind" in m.content and not m.is_live]
        assert retired and all(m.superseded_by for m in retired)
        # Episodes are permanently true and must NOT be retired.
        episodes = [
            m for m in store.all()
            if m.type is MemoryType.EPISODIC and "Northwind" in m.content
        ]
        assert episodes and all(m.is_live for m in episodes)


@pytest.mark.parametrize("profile", PROFILES)
def test_contradictions(built, profile) -> None:
    store, pipeline = built[profile]
    pairs = [("does not drink coffee", "three coffees"),
             ("detailed explanations", "shorter answers")]

    for a, b in pairs:
        live = {m.content for m in live_semantic(store, a, b)}
        if not pipeline.live_only:
            assert len(live) == 2, f"both sides of {a!r}/{b!r} live"
        else:
            assert len(live) == 1, f"{a!r}/{b!r} unresolved"
            retired = [m for m in store.all() if (a in m.content or b in m.content)
                       and not m.is_live]
            assert retired, "the loser must be retired, never absent"
            assert all(m.superseded_by for m in retired)


# --- failure 3: a refinement is not a contradiction -------------------------
@pytest.mark.parametrize("profile", PROFILES)
def test_refinement(built, profile) -> None:
    store, pipeline = built[profile]
    live = {m.content for m in live_semantic(store, "vegetarian", "fish", "meat")}

    if not pipeline.live_only:
        assert "Priya is vegetarian" in live and "Priya eats fish" in live
    else:
        assert "Priya is vegetarian" not in live, "narrowed by the pescatarian update"
        assert "Priya eats fish" in live
        assert any("does not eat meat" in c for c in live), (
            "the constraint that still holds must survive the update"
        )


# --- failure 4: entity fragmentation ----------------------------------------
# fixed by entity resolution (I2), detected via pipeline.resolve
@pytest.mark.parametrize("profile", PROFILES)
def test_entity_fragmentation(built, profile) -> None:
    store, pipeline = built[profile]
    text = " ".join(m.content for m in store.all())
    # Resolution LINKS; it never rewrites content. The strings stay either way.
    assert "Samira" in text and "Sammy" in text

    partner = [m for m in store.all()
               if any(n in m.content for n in ("Sam ", "Sam's", "Samira", "Sammy"))]
    # Resolution needs the whole store, so it runs as a consolidation pass.
    if pipeline.consolidate is None:
        assert all(not m.entities for m in partner), "nothing links them"
    else:
        canonical = {e for m in partner for e in m.entities}
        assert len(canonical) == 1, f"one person, one entity id, got {canonical}"
        pronoun = [m for m in store.all() if m.content.startswith("She works nights")]
        assert pronoun and set(pronoun[0].entities) == canonical, (
            "the bare pronoun resolves to the same person"
        )


# --- failure 5: hearsay promoted to belief ---------------------------------
# Only testable once I1 admits agent_writes.jsonl; fixed by arbitration (I4).
@pytest.mark.parametrize("profile", PROFILES)
def test_hearsay_is_not_believed(built, profile) -> None:
    store, pipeline = built[profile]
    berlin = [m for m in store.all() if "Berlin" in m.content]

    if not pipeline.ingest_agent_writes:
        assert berlin == [], "the beginner pipeline never sees shared-scope writes"
        return

    # Present -- refusing to store it would make a later confirmation look like
    # the first anyone had heard.
    assert len(berlin) == 1
    claim = berlin[0]
    assert claim.provenance.speaker == "travel-agent"
    assert claim.provenance.authority == 0.3
    assert claim.confidence == 0.3, "believed no more than its source is trusted"

    if pipeline.live_only:
        # ...and demoted: retired on authority, not on date. It is NEWER than
        # the address it lost to, so recency alone would have believed it.
        assert not claim.is_live and claim.superseded_by
        address = next(m for m in store.all() if "Halloway Road" in m.content)
        assert address.is_live
        assert claim.happened_at > address.happened_at, "the newer claim lost"
        assert "Berlin" not in str(exam_answer(store.all(), PRIYA).evidence)
    else:
        assert claim.is_live, "nothing has arbitrated yet"


def test_an_unresolved_pronoun_is_stored_as_a_fact(built) -> None:
    store, _ = built["beginner"]
    assert any(m.content.startswith("She works nights") for m in store.all())


# --- failures 5-7: correctly still broken through Milestone 2a --------------
def test_pii_is_stored_with_no_gate(built) -> None:
    for profile in PROFILES:
        text = " ".join(m.content for m in built[profile][0].all())
        assert "47 Halloway Road" in text and "07700 900412" in text


def test_the_deletion_request_is_not_honoured(built) -> None:
    """Compliance, not quality. The cascade lands in Advanced.

    I1's durability gate does fix half of this: an imperative is no longer
    filed as though it were a fact. The part that matters is untouched --
    Priya asked for the address to be forgotten and it is still there, in
    both profiles. Half a compliance failure is a compliance failure.
    """
    for profile in PROFILES:
        store, pipeline = built[profile]
        contents = [m.content for m in store.all()]
        filed = "Priya asked to forget her old address" in contents

        if pipeline.extract is get("beginner").extract:
            assert filed, "the naive extractor stores the request as a fact"
        else:
            assert not filed, "the gate routes imperatives away from the store"

        assert any("47 Halloway Road" in c for c in contents), (
            "and in neither case was anything actually deleted"
        )


def test_nothing_can_be_forgotten(built) -> None:
    """Salience and decay land in I5."""
    for profile in PROFILES:
        store = built[profile][0]
        assert {m.salience for m in store.all()} == {0.5}
        assert {m.access_count for m in store.all()} == {0}


# --- the exam ----------------------------------------------------------------
def test_consolidation_is_idempotent(built) -> None:
    """Re-running the write path must not change what the system believes."""
    for profile in PROFILES:
        store, pipeline = built[profile]
        if pipeline.consolidate is None:
            continue
        once = pipeline.consolidate(store.all())
        twice = pipeline.consolidate(once)
        assert [(m.id, m.confidence, m.invalid_at) for m in once] == [
            (m.id, m.confidence, m.invalid_at) for m in twice
        ]


@pytest.mark.parametrize("profile", PROFILES)
def test_the_exam(built, profile) -> None:
    store, pipeline = built[profile]
    answer = exam_answer(store.all(), PRIYA)

    if not pipeline.live_only:
        assert answer.employer == "Northwind Labs", "the dead fact outranks the live one"
        assert "fish" not in answer.permitted, "vegetarian and eats-fish both live"
        assert not answer.is_correct
    else:
        assert answer.employer == "Calico Systems"
        assert answer.avoid == {"meat", "gluten"}
        assert "fish" in answer.permitted
        assert answer.is_correct
