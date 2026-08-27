"""What decays is relevance, not truth. Asserted."""
from __future__ import annotations

from collections import Counter

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.eval.exam import exam_answer
from memlab.fixtures import load_turns
from memlab.forget import budget
from memlab.forget.salience import apply as score_salience
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope, Tier

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

DECAY_RATE = _solution.DECAY_RATE
HALF_LIFE = _solution.HALF_LIFE
apply = _solution.apply
reference_now = _solution.reference_now
tier_for = _solution.tier_for
uniform_apply = _solution.uniform_apply

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def scored(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("dec") / "m.jsonl")
    ingest(store, PRIYA, at("I4"))
    turns = {f"s{t['session']}:{t['ts']}": t["text"] for t in load_turns(user_only=True)}
    return score_salience(store.all(), turns)


def dropped(memories):
    return [m for m in memories if m.is_live and m.tier is not Tier.LONG_TERM]


def test_stub_is_runnable(scored) -> None:
    with pytest.raises(NotImplementedError):
        _lab.decayed(scored[0], reference_now(scored))


def test_the_half_life_is_180_days() -> None:
    assert HALF_LIFE.days == 180


def test_a_uniform_rate_drops_standing_beliefs(scored) -> None:
    """The modelling error, measured by what leaves rather than how much."""
    out = uniform_apply(scored)
    kinds = Counter(m.type.value for m in dropped(out))
    assert kinds["semantic"] == 14
    assert kinds["procedural"] == 2
    assert len(budget.retrievable(out)) == 7


def test_and_breaks_the_exam(scored) -> None:
    assert not exam_answer(budget.retrievable(uniform_apply(scored)), PRIYA).is_correct


def test_scaling_by_type_keeps_the_beliefs(scored) -> None:
    out = apply(scored)
    kinds = Counter(m.type.value for m in dropped(out))
    assert kinds["semantic"] == 5
    assert kinds["procedural"] == 0
    assert len(budget.retrievable(out)) == 18


def test_and_the_exam_survives(scored) -> None:
    assert exam_answer(budget.retrievable(apply(scored)), PRIYA).is_correct


def test_most_episodes_fall_out(scored) -> None:
    out = apply(scored)
    episodes = [m for m in out if m.is_live and m.type is MemoryType.EPISODIC]
    demoted = [m for m in episodes if m.tier is not Tier.LONG_TERM]
    assert (len(demoted), len(episodes)) == (7, 9)


def test_the_two_survivors_and_why(scored) -> None:
    """One is genuinely recent. The other is mis-dated, and decay cannot know.

    "Priya used to cycle to work before the move" describes 2025 and carries
    happened_at = 2026-04-08, the date of the TURN -- extraction never
    backdated it. Decay reads event time and correctly concludes it is recent,
    so a past-tense episode sits in long_term looking current.

    A downstream stage cannot repair this; the fix is relative-time-resolution
    in Advanced. Worth pinning here so the defect is visible rather than
    absorbed.
    """
    out = apply(scored)
    survivors = {
        m.content: m for m in out
        if m.is_live and m.type is MemoryType.EPISODIC and m.tier is Tier.LONG_TERM
    }
    assert len(survivors) == 2
    cycling = next(m for c, m in survivors.items() if "used to cycle" in c)
    assert cycling.happened_at.date().isoformat() == "2026-04-08"


def test_beliefs_decay_slower_than_episodes() -> None:
    assert DECAY_RATE[MemoryType.EPISODIC] > DECAY_RATE[MemoryType.SEMANTIC]
    assert DECAY_RATE[MemoryType.SEMANTIC] > DECAY_RATE[MemoryType.PROCEDURAL]


def test_nothing_is_removed(scored) -> None:
    assert len(apply(scored)) == len(scored) == 37


def test_decay_is_deterministic(scored) -> None:
    """Reference time comes from the corpus, so two runs agree."""
    once, twice = apply(scored), apply(scored)
    assert [m.salience for m in once] == [m.salience for m in twice]


def test_tier_bands_are_wide(scored) -> None:
    assert tier_for(0.41) is Tier.LONG_TERM
    assert tier_for(0.25) is Tier.WORKING
    assert tier_for(0.10) is Tier.SCRATCH
