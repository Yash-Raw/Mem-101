"""Slots find what similarity cannot. Asserted."""
from __future__ import annotations

from collections import Counter

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.evolve.conflict import Relation
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

candidates = _solution.candidates
classify = _solution.classify
known_similarities = _solution.known_similarities
similarity_candidates = _solution.similarity_candidates
slot_of = _solution.slot_of

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("conf") / "m.jsonl")
    ingest(store, PRIYA, at("I3"))
    return store.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.slot_of(memories[0])


def test_the_employer_contradiction_scores_below_noise() -> None:
    """The measurement the whole lesson rests on."""
    scored = {label if label == "NOISE" else a[:20]: s
              for s, a, b, label in known_similarities()}
    employer = next(s for s, a, _, _ in known_similarities() if "data engineer" in a)
    assert employer == pytest.approx(0.285, abs=0.01)
    assert employer < scored["NOISE"], "unrelated beliefs look more alike than these"


def test_slot_grouping_finds_it(memories) -> None:
    pairs = candidates(memories, PRIYA)
    found = [
        (a, b) for a, b, slot in pairs
        if slot == "employer" and "Northwind" in a.content and "Calico" in b.content
    ]
    assert found, "slot grouping surfaces the pair similarity buries"


def test_similarity_at_a_usable_threshold_misses_it(memories) -> None:
    pairs = similarity_candidates(memories, PRIYA, 0.45)
    assert not any(
        "Northwind" in a.content and "Calico" in b.content for a, b in pairs
    ), "no usable similarity threshold generates the pair that matters"


def test_slots_generate_fewer_candidates(memories) -> None:
    assert len(candidates(memories, PRIYA)) == 24
    assert len(similarity_candidates(memories, PRIYA, 0.35)) > 24


def test_most_same_slot_pairs_are_compatible(memories) -> None:
    """Sharing an attribute is what makes two claims worth comparing."""
    relations = Counter(classify(a, b) for a, b, _ in candidates(memories, PRIYA))
    assert relations[Relation.COMPATIBLE] == 15
    assert relations[Relation.CONTRADICTION] == 6
    assert relations[Relation.REFINEMENT] == 2
    assert relations[Relation.DUPLICATE] == 1


def test_refinement_and_contradiction_are_distinguished(memories) -> None:
    def find(x: str, y: str):
        return next(
            classify(a, b) for a, b, _ in candidates(memories, PRIYA)
            if x in a.content and y in b.content
        )

    assert find("is vegetarian", "is pescatarian") is Relation.REFINEMENT
    assert find("does not drink coffee", "three coffees") is Relation.CONTRADICTION


def test_hearsay_contradicts_a_first_party_fact(memories) -> None:
    relation = next(
        classify(a, b) for a, b, slot in candidates(memories, PRIYA)
        if slot == "residence"
    )
    assert relation is Relation.CONTRADICTION
