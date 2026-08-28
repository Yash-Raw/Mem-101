"""Label, do not decide -- and measure what deciding at the gate costs."""
from __future__ import annotations

from dataclasses import replace as dc_replace

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.eval.exam import exam_answer
from memlab.fixtures import load_gold
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Kind = _solution.Kind
blocked_by = _solution.blocked_by
classify = _solution.classify
scan = _solution.scan

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("pw") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    return s.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.scan(memories)


def test_every_gold_pii_item_is_in_the_store(memories) -> None:
    for item in load_gold()["pii"]:
        needle = item["value"].split(",")[0]
        assert any(needle in m.content for m in memories), item["kind"]


def test_seven_memories_carry_personal_data(memories) -> None:
    findings = scan(memories)
    assert len(findings) == 7
    assert sum(1 for f in findings if not f.about_the_user) == 3


def test_both_health_memories_are_labelled(memories) -> None:
    """Labelling the semantic fact and missing the episode is half the data."""
    health = [f for f in scan(memories) if f.kind is Kind.HEALTH]
    assert len(health) == 2
    assert any("diagnosed" in f.memory.content for f in health)
    assert any("has a gluten intolerance" in f.memory.content for f in health)


def test_blocking_everything_breaks_the_exam(memories) -> None:
    findings = scan(memories)
    dropped = {m.id for m in blocked_by(findings, set(Kind))}
    kept = [m for m in memories if m.id not in dropped]
    assert len(dropped) == 7
    assert len(kept) == 30
    assert not exam_answer(kept, PRIYA).is_correct
    assert exam_answer(memories, PRIYA).is_correct


@pytest.mark.parametrize(
    "kinds,blocked",
    [
        (set(), 0),
        ({Kind.ADDRESS, Kind.PHONE}, 2),
        ({Kind.THIRD_PARTY_HEALTH}, 3),
    ],
)
def test_narrow_policies_preserve_the_exam(memories, kinds, blocked) -> None:
    findings = scan(memories)
    dropped = {m.id for m in blocked_by(findings, kinds)}
    assert len(dropped) == blocked
    kept = [m for m in memories if m.id not in dropped]
    assert exam_answer(kept, PRIYA).is_correct


def test_the_blocked_health_fact_is_one_the_exam_needs(memories) -> None:
    findings = scan(memories)
    blocked = blocked_by(findings, {Kind.HEALTH})
    assert any("gluten" in m.content for m in blocked)


def test_third_party_is_detected_by_the_entity_link(memories) -> None:
    """The stretch: strip entities and two become health data about the user."""
    third_party = [f for f in scan(memories) if f.kind is Kind.THIRD_PARTY_HEALTH]
    assert all(f.memory.entities for f in third_party)

    stripped = [dc_replace(m, entities=()) for m in memories]
    kinds = [classify(m) for m in stripped if classify(m)]
    assert Kind.THIRD_PARTY_HEALTH not in kinds
