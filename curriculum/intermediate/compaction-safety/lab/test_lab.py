"""A policy derived from the question, and what it does not buy. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ask, ingest
from memlab.assemble.budget import pack
from memlab.eval.exam import QUESTION
from memlab.evolve.conflict import slot_of
from memlab.pipeline import at
from memlab.retrieve.query import slots_for
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

required = _solution.required
unpinned = _solution.unpinned

NEEDED = ("works at Calico", "does not eat meat", "eats fish", "gluten")
PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def hits(tmp_path_factory):
    pipeline = at("I7")
    store = JsonlStore(tmp_path_factory.mktemp("pn") / "m.jsonl")
    ingest(store, PRIYA, pipeline)
    pipeline.vectors.index(store.all())
    _ctx, hits = ask(store, PRIYA, QUESTION, k=5, pipeline=pipeline)
    return hits


def complete(hits, budget, pin) -> bool:
    out = pack(hits, budget_tokens=budget, pin=pin)
    return all(any(n in h.memory.content for h in out.kept) for n in NEEDED)


def test_stub_is_runnable(hits) -> None:
    with pytest.raises(NotImplementedError):
        _lab.required(hits)


def test_the_policy_is_derived_from_the_question(hits) -> None:
    """Not a topic list -- I5 measured what those cost."""
    asked = set().union(*(slots_for(h.query) for h in hits))
    assert asked == {"employer", "diet"}
    covered = {slot_of(h.memory) for h in required(hits)}
    assert asked <= covered


def test_coverage_is_breadth_first(hits) -> None:
    """A slot with one fact must not starve a slot with three."""
    slots = [slot_of(h.memory) for h in required(hits)]
    assert slots[:2] == ["diet", "employer"], "one from each before any second"


def test_pinning_changes_nothing_here(hits) -> None:
    """The third no-op in this module, and the reason the header is next."""
    for budget in (80, 77, 70, 67, 60):
        assert complete(hits, budget, pin=False) == complete(hits, budget, pin=True)


def test_because_depth_one_beats_depth_two(hits) -> None:
    order = [h.memory.content for h in required(hits)]
    staff = next(i for i, c in enumerate(order) if "staff engineer" in c)
    gluten = next(i for i, c in enumerate(order) if "gluten" in c)
    assert staff < gluten, "the employer slot's second fact precedes the diet slot's third"


def test_pinned_memories_still_have_to_fit(hits) -> None:
    """A context that exceeds the budget is not safer; it is undeliverable."""
    out = pack(hits, budget_tokens=45, pin=True)
    assert out.used <= 45


def test_unpinned_is_the_complement(hits) -> None:
    must = required(hits)
    rest = unpinned(hits, must)
    assert {h.memory.id for h in must} | {h.memory.id for h in rest} == {
        h.memory.id for h in hits
    }
    assert not ({h.memory.id for h in must} & {h.memory.id for h in rest})


def test_uneven_slots_are_where_it_matters(hits) -> None:
    """The stretch: breadth-first is the point when depth is uneven."""
    diet_only = [h for h in hits if slot_of(h.memory) == "diet"]
    employer = next(h for h in hits if "works at Calico" in h.memory.content)
    skewed = [*diet_only, employer]
    pinned = required(skewed)
    assert slot_of(pinned[1].memory) == "employer", (
        "the single employer fact is reached before the diet slot's second"
    )
