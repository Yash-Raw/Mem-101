"""Two of five tactics do not apply, and that is the deliverable."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.fixtures import load_turns

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

already_shipped = _solution.already_shipped
assess = _solution.assess
headroom = _solution.headroom

WRITE_CALLS, WRITE_EMBEDS, READ_CALLS = 48, 38, 0


@pytest.fixture(scope="module")
def tactics():
    return assess(WRITE_CALLS, WRITE_EMBEDS, READ_CALLS)


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.assess(48, 38, 0)


def test_three_of_five_apply(tactics) -> None:
    assert headroom(tactics) == (3, 5)


def test_the_completion_cache_never_hits() -> None:
    """24 turns, 24 distinct keys. Not a tuning problem."""
    turns = [t for t in load_turns(user_only=True) if t["session"] < 14]
    assert len(turns) == 24
    assert len({t["text"] for t in turns}) == 24


def test_caching_completions_is_marked_inapplicable(tactics) -> None:
    tactic = next(t for t in tactics if t.name == "cache completions")
    assert not tactic.applies
    assert tactic.saving == "nothing"
    assert "never repeats" in tactic.why


def test_the_embedding_cache_was_already_shipped(tactics) -> None:
    """I7 built it for a scaling reason; the cost saving is the same code."""
    assert already_shipped(tactics) == ["cache embeddings"]


def test_warm_and_cold_reads_differ_by_eighteen_embeddings(tmp_path) -> None:
    """The saving the tactic claims, measured."""
    from memlab.app.chat import ask, ingest
    from memlab.cost.profile import counting
    from memlab.eval.exam import QUESTION
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    costs = {}
    for indexed in (True, False):
        pipeline = at("A3")
        store = JsonlStore(tmp_path / f"c-{indexed}.jsonl")
        store.clear()
        ingest(store, scope, pipeline)
        if indexed:
            pipeline.vectors.index(store.all())
        with counting() as counts:
            ask(store, scope, QUESTION, k=5, pipeline=pipeline)
        costs[indexed] = counts["embed"]

    assert (costs[True], costs[False]) == (2, 20)
    assert costs[False] - costs[True] == 18


def test_routing_arbitration_has_no_call_to_route(tactics) -> None:
    tactic = next(t for t in tactics if t.name == "route arbitration")
    assert not tactic.applies
    assert "rules" in tactic.why


def test_arbitration_really_makes_no_model_call() -> None:
    """The claim, checked against the file it is about."""
    import pathlib

    import memlab

    source = (
        pathlib.Path(memlab.__file__).parent / "evolve" / "arbitrate.py"
    ).read_text()
    assert "client.complete" not in source


def test_batching_reports_the_unit(tactics) -> None:
    """Fewer calls over the same tokens; which one the bill uses varies."""
    tactic = next(t for t in tactics if t.name == "batch extraction")
    assert "same work" in tactic.saving
    assert "backfill" in tactic.why


def test_routing_targets_the_blocking_cost(tactics) -> None:
    tactic = next(t for t in tactics if t.name.startswith("route extraction"))
    assert tactic.applies
    assert "81%" in tactic.saving
