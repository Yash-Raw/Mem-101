"""Stage, measure, promote or roll back -- and rollback is built first."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.eval.exam import exam_answer, exam_from_context
from memlab.pipeline import at
from memlab.sleep.reflect import reflect
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

evaluate = _solution.evaluate
preview = _solution.preview
promote = _solution.promote
rollback = _solution.rollback
stage = _solution.stage

PRIYA = Scope(user="priya")
NOW = datetime(2026, 8, 27, tzinfo=UTC)


def _fingerprint(memories):
    return sorted(
        (m.id, m.invalid_at, m.superseded_by, m.valid_to, m.tier.value)
        for m in memories
    )


@pytest.fixture
def env(tmp_path):
    pipeline = at("A2")
    store = JsonlStore(tmp_path / "release.jsonl")
    store.clear()
    ingest(store, PRIYA, pipeline)

    def lowest_passing(memories):
        for budget in range(40, 90):
            if exam_from_context(
                memories, PRIYA, k=5, pipeline=pipeline, budget=budget
            ).is_correct:
                return budget
        return None

    return store, pipeline, lowest_passing


def _staged(store):
    return stage(store.all(), lambda ms: reflect(ms, PRIYA), NOW)


def test_stub_is_runnable(env) -> None:
    store, _p, _l = env
    with pytest.raises(NotImplementedError):
        _lab.stage(store.all(), lambda ms: reflect(ms, PRIYA), NOW)


def test_the_retirement_set_is_read_off_the_provenance(env) -> None:
    """Specified separately, the two would drift apart."""
    store, _p, _l = env
    staged = _staged(store)
    assert len(staged.added) == 3
    assert len(staged.retired) == 8
    assert set(staged.retired) == {i for m in staged.added for i in m.derived_from}
    assert len(staged.base_ids) == 37


def test_staging_touches_nothing(env) -> None:
    store, _p, _l = env
    before = _fingerprint(store.all())
    _staged(store)
    assert _fingerprint(store.all()) == before


def test_the_verdict_measures_headroom_not_pass_fail(env) -> None:
    """The exam still answers correctly; it just costs five more tokens."""
    store, pipeline, lowest = env
    staged = _staged(store)
    after = preview(store.all(), staged, NOW, pipeline.decay)
    verdict = evaluate(store.all(), after, lowest)
    assert (verdict.before, verdict.after, verdict.delta) == (51, 56, 5)
    assert not verdict.better
    assert exam_answer(after, PRIYA).is_correct, "green on a pass/fail check"


def test_a_preview_without_the_finalize_step_is_a_different_program(env) -> None:
    """Scored in the preview, tier=working on disk, sources already retired."""
    store, pipeline, lowest = env
    staged = _staged(store)
    assert lowest(preview(store.all(), staged, NOW, None)) is None
    assert lowest(preview(store.all(), staged, NOW, pipeline.decay)) == 56


def test_promote_writes_what_the_preview_measured(env) -> None:
    store, pipeline, lowest = env
    staged = _staged(store)
    expected = lowest(preview(store.all(), staged, NOW, pipeline.decay))
    promote(store, staged, NOW, pipeline.decay)
    assert lowest(store.all()) == expected == 56


def test_rollback_restores_the_store_exactly(env) -> None:
    """Possible only because supersession never deleted anything."""
    store, pipeline, lowest = env
    before = _fingerprint(store.all())
    staged = _staged(store)
    promote(store, staged, NOW, pipeline.decay)
    assert _fingerprint(store.all()) != before
    rollback(store, staged)
    assert _fingerprint(store.all()) == before
    assert lowest(store.all()) == 51


def test_the_round_trip_is_repeatable(env) -> None:
    store, pipeline, _l = env
    before = _fingerprint(store.all())
    for _ in range(2):
        staged = _staged(store)
        promote(store, staged, NOW, pipeline.decay)
        rollback(store, staged)
        assert _fingerprint(store.all()) == before


def test_promotion_refuses_a_moved_base(env) -> None:
    store, pipeline, _l = env
    staged = _staged(store)
    store.replace(store.all()[:-1])
    with pytest.raises(ValueError, match="base has moved"):
        promote(store, staged, NOW, pipeline.decay)


def test_a_deleting_store_could_not_roll_back(env) -> None:
    """The information rollback needs would not exist anywhere."""
    store, pipeline, _l = env
    staged = _staged(store)
    promote(store, staged, NOW, pipeline.decay)
    subsumed = [m for m in store.all() if m.id in set(staged.retired)]
    assert len(subsumed) == 8, "retired, still present, still carrying their content"
    assert all(m.superseded_by for m in subsumed)
