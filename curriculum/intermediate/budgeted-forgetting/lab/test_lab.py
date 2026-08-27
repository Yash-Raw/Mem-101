"""The cap is a correctness parameter. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.eval.exam import exam_answer
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope, Tier

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

DEFAULT_CAP = _solution.DEFAULT_CAP
cap_sweep = _solution.cap_sweep
enforce = _solution.enforce
retrievable = _solution.retrievable

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("bud") / "m.jsonl")
    ingest(store, PRIYA, at("I5"))
    return store.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.enforce(memories, cap=5)


def test_the_cap_does_not_bind_yet(memories) -> None:
    """Pinned so the headroom is visible rather than assumed."""
    assert len(retrievable(memories)) == 18
    assert DEFAULT_CAP == 20
    _, evictions = enforce(memories, cap=DEFAULT_CAP)
    assert evictions == []


def test_eviction_never_removes_anything(memories) -> None:
    for cap in (16, 12, 8, 1):
        out, _ = enforce(memories, cap=cap)
        assert len(out) == len(memories) == 37


def test_eviction_demotes_one_step(memories) -> None:
    _, evictions = enforce(memories, cap=8)
    assert evictions
    assert all(e.from_tier is Tier.LONG_TERM for e in evictions)
    assert all(e.to_tier is Tier.WORKING for e in evictions), (
        "one step, so reinforcement can lift it back"
    )


def test_tightening_the_cap_by_four_breaks_the_exam(memories) -> None:
    """The lesson's central measurement."""
    rows = {cap: (ok, avoid) for cap, _, _, ok, avoid, _ in cap_sweep(memories)}
    assert rows[20][0] is True
    assert rows[16][0] is False
    assert rows[16][1] == ["gluten"], "it forgets she does not eat meat"


def test_the_casualty_is_named(memories) -> None:
    lost = next(lost for cap, _, _, _, _, lost in cap_sweep(memories) if cap == 16)
    assert "Priya does not eat meat" in lost


def test_the_evicted_fact_is_still_in_the_log(memories) -> None:
    """Broken answer, recoverable store. That is the whole point of demoting."""
    out, _ = enforce(memories, cap=16)
    meat = next(m for m in out if m.content == "Priya does not eat meat")
    assert meat.is_live and meat not in retrievable(out)


def test_protecting_a_class_helps_and_does_not_solve_it(memories) -> None:
    """The stretch, and its honest result.

    Make dietary facts unevictable and the diet survives a cap of 10 -- but the
    EMPLOYER is evicted instead, so the exam still fails. Class-based protection
    only defends the classes you thought of, and the set of facts a question
    depends on is not known in advance. That is the real shape of
    compaction-safety, and it is why the answer there is a budget policy rather
    than a list.
    """
    protected = {m.id for m in memories if "eat" in m.content or "gluten" in m.content}
    out, _ = enforce([m for m in memories if m.id not in protected], cap=10)
    kept = retrievable(out) + [m for m in memories if m.id in protected and m.is_live]

    answer = exam_answer(kept, PRIYA)
    assert answer.avoid == {"meat", "gluten"} and "fish" in answer.permitted
    assert answer.employer is None, "the employer was evicted in the diet's place"
    assert not answer.is_correct
