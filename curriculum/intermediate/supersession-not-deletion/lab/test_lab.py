"""The exam flips, and the history survives. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.eval.exam import exam_answer
from memlab.pipeline import at, get
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

reconcile = _solution.reconcile

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("sup") / "m.jsonl")
    ingest(store, PRIYA, at("I3"))
    return reconcile(store.all(), PRIYA)


@pytest.fixture(scope="module")
def by_profile(tmp_path_factory):
    out = {}
    root = tmp_path_factory.mktemp("exam")
    for name, pipeline in [("beginner", get("beginner")), ("@I1", at("I1")),
                           ("@I2", at("I2")), ("@I3", at("I3")), ("@I4", at("I4"))]:
        store = JsonlStore(root / f"{name}.jsonl")
        ingest(store, PRIYA, pipeline)
        out[name] = store.all()
    return out


def test_stub_is_runnable(by_profile) -> None:
    with pytest.raises(NotImplementedError):
        _lab.reconcile(by_profile["@I3"], PRIYA)


def test_seven_retired_none_deleted(result) -> None:
    assert len(result.memories) == 37
    assert len(result.retired) == 7
    assert sum(1 for m in result.memories if m.is_live) == 30


def test_a_merge_actually_merges(result) -> None:
    """One fact, one live record -- the restatement retired, not left beside it."""
    nights = [m for m in result.memories if "works nights" in m.content]
    assert len(nights) == 2
    assert sum(1 for m in nights if m.is_live) == 1
    survivor = next(m for m in nights if m.is_live)
    assert survivor.confidence > 0.9, "and corroborated by the one it absorbed"


def test_consolidation_is_idempotent(by_profile) -> None:
    """The standard semantic-drift set for compaction, applied to the whole pass."""
    pipeline = at("I4")
    once = pipeline.consolidate(by_profile["@I3"])
    twice = pipeline.consolidate(once)
    key = lambda ms: [(m.id, m.confidence, m.invalid_at, m.derived_from) for m in ms]
    assert key(once) == key(twice)


def test_every_retirement_points_at_its_replacement(result) -> None:
    for m in result.retired:
        assert m.invalid_at is not None
        assert m.superseded_by, "a retired belief must name what replaced it"
        assert m.content, "and keep its content"


def test_invalid_at_is_the_winners_event_time(result) -> None:
    """Not the moment the job ran -- that would inject false history."""
    northwind = next(m for m in result.retired if "data engineer at Northwind" in m.content)
    assert northwind.invalid_at.date().isoformat() == "2025-12-08"


def test_no_episode_is_ever_retired(result) -> None:
    """typed-memory-model made this structural, not a special case here."""
    episodes = [m for m in result.memories if m.type is MemoryType.EPISODIC]
    assert episodes
    assert all(m.is_live for m in episodes)
    assert any("Northwind" in m.content for m in episodes)


def test_the_exam_flips_only_at_i4(by_profile) -> None:
    """The headline result of the whole milestone."""
    for name in ("beginner", "@I1", "@I2", "@I3"):
        answer = exam_answer(by_profile[name], PRIYA)
        assert answer.employer == "Northwind Labs"
        assert not answer.is_correct

    final = exam_answer(by_profile["@I4"], PRIYA)
    assert final.employer == "Calico Systems"
    assert final.avoid == {"meat", "gluten"}
    assert "fish" in final.permitted
    assert final.is_correct


def test_supersession_removes_the_wrong_answer_but_does_not_rank_the_right_one(by_profile) -> None:
    """Honest scope: a belief fix, not a ranking fix. I6 handles the rest."""
    from memlab.eval.exam import QUESTION
    from memlab.retrieve.embedding import EmbeddingRetriever

    memories = [m for m in by_profile["@I4"] if m.is_live]
    hits = EmbeddingRetriever().search(QUESTION, memories, PRIYA, k=len(memories))

    def rank(needle: str) -> int | None:
        return next((i for i, h in enumerate(hits, 1) if needle in h.memory.content), None)

    assert rank("data engineer at Northwind") is None, "the stale fact no longer competes"
    calico = rank("works at Calico Systems")
    assert calico is not None and calico > 10, (
        "and the correct one is still buried -- that is a ranking problem"
    )


def test_the_history_is_still_answerable(result) -> None:
    """The difference between superseding and deleting."""
    before = [
        m for m in result.memories
        if not m.is_live and "Northwind" in m.content and m.type is MemoryType.SEMANTIC
    ]
    assert before, "'where did I work before Calico?' must still have an answer"


def test_deleting_would_pass_the_exam_and_lose_the_history(by_profile) -> None:
    """Both implementations pass the headline test. Only one is right."""
    deleted = _solution.reconcile_by_deleting(by_profile["@I3"], PRIYA)
    assert exam_answer(deleted, PRIYA).is_correct, "the exam alone cannot tell them apart"
    assert not [
        m for m in deleted
        if "Northwind" in m.content and m.type is MemoryType.SEMANTIC
    ], "and the history is gone"
