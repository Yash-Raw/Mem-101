"""The line format has a price. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ask, ingest
from memlab.assemble.simple import HEADER, estimate_tokens
from memlab.assemble.value import COMPACT_HEADER
from memlab.eval.exam import QUESTION
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

BARE, DATED, YEAR = _solution.BARE, _solution.DATED, _solution.YEAR
order = _solution.order
render = _solution.render

NEEDED = ("works at Calico", "does not eat meat", "eats fish", "gluten")
PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def hits(tmp_path_factory):
    pipeline = at("I7")
    store = JsonlStore(tmp_path_factory.mktemp("or") / "m.jsonl")
    ingest(store, PRIYA, pipeline)
    pipeline.vectors.index(store.all())
    _ctx, hits = ask(store, PRIYA, QUESTION, k=5, pipeline=pipeline)
    return hits


@pytest.fixture(scope="module")
def needed(hits):
    return [h for h in hits if any(n in h.memory.content for n in NEEDED)]


def cost(needed, precision) -> int:
    return sum(estimate_tokens(render(h, precision)) for h in needed)


def test_stub_is_runnable(hits) -> None:
    with pytest.raises(NotImplementedError):
        _lab.render(hits[0])


def test_the_three_formats_are_priced(needed) -> None:
    assert (cost(needed, DATED), cost(needed, YEAR), cost(needed, BARE)) == (38, 32, 25)


def test_year_precision_returns_six_tokens(needed) -> None:
    assert cost(needed, DATED) - cost(needed, YEAR) == 6


def test_the_floor_with_each_header(needed) -> None:
    assert cost(needed, DATED) + estimate_tokens(HEADER) == 67
    assert cost(needed, YEAR) + estimate_tokens(COMPACT_HEADER) == 43


def test_dated_is_still_the_default() -> None:
    """Nothing before I8 changes; the assembler opts in explicitly."""
    import inspect

    assert inspect.signature(render).parameters["precision"].default == DATED


def test_an_undated_memory_renders_bare(hits) -> None:
    from dataclasses import replace

    undated = replace(hits[0], memory=replace(hits[0].memory, happened_at=None))
    assert render(undated, DATED).startswith("- Priya")


def test_score_and_chronological_order_agree_here(hits) -> None:
    """Honest: the principle is sound and this corpus cannot demonstrate it."""
    by_score = order(hits)
    by_time = sorted(hits, key=lambda h: h.memory.happened_at)
    assert [h.memory.id for h in by_score] == [h.memory.id for h in by_time]


def test_order_is_by_descending_score(hits) -> None:
    scores = [h.score for h in order(hits)]
    assert scores == sorted(scores, reverse=True)
