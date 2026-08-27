"""Drift is geometric, and re-derivation is idempotent. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

compact = _solution.compact
drift_curve = _solution.drift_curve
is_idempotent = _solution.is_idempotent
rederive_curve = _solution.rederive_curve


@pytest.fixture(scope="module")
def sources(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("drift") / "m.jsonl")
    ingest(store, Scope(user="priya"), at("I3"))
    return [m for m in store.all() if m.type is MemoryType.SEMANTIC and m.is_live]


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.compact("a; b; c")


def test_the_naive_loop_decays_geometrically(sources) -> None:
    curve = drift_curve(sources)
    recoverable = [p.recoverable for p in curve]
    assert recoverable[0] == 1.0
    assert recoverable == sorted(recoverable, reverse=True)
    assert recoverable[-1] < 0.25, "four rounds at 70% leaves under a quarter"


def test_the_loss_is_worse_than_the_ratio(sources) -> None:
    """Round 2 is not 70% -- it is 70% of 70%."""
    curve = drift_curve(sources)
    assert curve[1].recoverable == pytest.approx(0.70, abs=0.03)
    assert curve[2].recoverable < 0.5


def test_rederivation_is_flat(sources) -> None:
    curve = rederive_curve(sources)
    levels = {round(p.recoverable, 3) for p in curve[1:]}
    assert len(levels) == 1, "every round gives the same result"
    assert curve[-1].recoverable == pytest.approx(0.70, abs=0.03)


def test_same_ratio_same_summariser_different_outcome(sources) -> None:
    """The only difference is what gets fed back in."""
    naive, rederived = drift_curve(sources), rederive_curve(sources)
    assert naive[1].claims == rederived[1].claims, "round one is identical"
    assert naive[-1].claims < rederived[-1].claims, "and then they diverge"


def test_only_rederivation_is_idempotent(sources) -> None:
    assert is_idempotent(sources)
    curve = drift_curve(sources, rounds=2)
    assert curve[1].claims != curve[2].claims, "the naive loop is not"


def test_compaction_always_keeps_at_least_one_claim() -> None:
    assert compact("only one claim", keep=0.1) == "only one claim"
