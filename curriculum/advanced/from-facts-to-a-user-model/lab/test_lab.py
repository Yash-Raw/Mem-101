"""Six attributes, five already wrong once, and six facts that cannot fit."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.evolve.conflict import slot_of
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

build = _solution.build

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("um") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    return s.all()


@pytest.fixture(scope="module")
def model(memories):
    return build(memories, PRIYA)


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.build(memories, PRIYA)


def test_the_naive_model_against_the_keyed_one(memories, model) -> None:
    naive = [m for m in memories if m.type is MemoryType.SEMANTIC and m.is_live]
    assert len(naive) == 19
    assert len(model.attributes) == 6
    assert len(model.unkeyed) == 6
    assert len(model.third_party) == 2
    assert len(model.unkeyed) + len(model.third_party) + sum(
        len(a.beliefs) for a in model.attributes.values()
    ) == len(naive)


def test_five_of_six_attributes_have_already_changed(model) -> None:
    assert model.volatile == (
        "beverage", "diet", "employer", "residence", "response_style"
    )
    assert model.stable == ("commute",)


def test_the_stable_one_is_stable_by_accident(model, memories) -> None:
    """One opportunity to vary, and it did not take it."""
    commute = model.attributes["commute"]
    assert commute.superseded == 0
    moves = [
        m for m in memories
        if slot_of(m) == "residence" and not m.entities
    ]
    assert len(moves) >= 2, "she moved once; the commute changed once"


def test_a_partners_job_is_not_in_the_model(model) -> None:
    assert all("Samira" in m.content or "Sam " in m.content for m in model.third_party)
    assert "occupation_other" not in model.attributes


def test_volatility_is_counted_over_the_user_only(memories, model) -> None:
    """The stretch: occupation_other has the most churn and is not the user's."""
    third_party_churn = sum(
        1 for m in memories
        if not m.is_live and m.entities and slot_of(m) == "occupation_other"
    )
    assert third_party_churn == 2
    assert max(a.superseded for a in model.attributes.values()) == 1


def test_what_cannot_enter_is_returned_not_dropped(model) -> None:
    contents = [m.content for m in model.unkeyed]
    assert "Priya's phone number is 07700 900412" in contents
    assert any("recurring 1:1" in c for c in contents), "the calendar agent's writes"
    assert all(slot_of(m) is None for m in model.unkeyed)


def test_the_model_excludes_pii_by_accident(model) -> None:
    """No slot for a phone number -- which A6 has to turn into a decision."""
    in_model = [v for a in model.attributes.values() for v in a.values]
    assert not any("07700 900412" in v for v in in_model)
    assert any("07700 900412" in m.content for m in model.unkeyed)


def test_diet_stays_four_beliefs(model) -> None:
    """All true at once; composing them measured worse under a budget."""
    assert len(model.attributes["diet"].beliefs) == 4
