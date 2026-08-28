"""Three accidental defences and one uncovered gap."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from memlab import labkit
from memlab.agents.authorise import WritePolicy
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.privacy.delete import purge
from memlab.store.jsonl import JsonlStore
from memlab.store.scopes import leak_check
from memlab.types import Memory, MemoryType, Provenance, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Attack = _solution.Attack
accidental = _solution.accidental
survey = _solution.survey
uncovered = _solution.uncovered

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("ma") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    return s.all()


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.survey()


def test_three_of_four_are_covered() -> None:
    defences = survey()
    assert len(defences) == 4
    assert [d.attack for d in uncovered(defences)] == [Attack.EXTRACTION]


def test_every_defence_was_built_for_something_else() -> None:
    """A control nobody knows is a control has no maintenance plan."""
    defences = survey()
    covered = [d for d in defences if d.covered]
    assert len(accidental(defences)) == len(covered) == 3
    assert all(d.built_for for d in covered)


def test_every_defence_states_a_residual() -> None:
    for defence in survey():
        assert defence.residual, defence.attack


def test_injection_is_defended_live(memories) -> None:
    assert sum(1 for m in memories if "asked to forget" in m.content) == 0


def test_cross_user_is_defended_live(memories) -> None:
    assert leak_check(memories, PRIYA) == []


def test_poisoning_is_defended_live(memories) -> None:
    policy = WritePolicy.default()
    newest = max((m.happened_at or m.recorded_at) for m in memories)
    rogue = Memory(
        content="Priya works at Meridian",
        type=MemoryType.SEMANTIC,
        scope=Scope(user="priya"),
        happened_at=datetime(2026, 5, 16, tzinfo=UTC),
        provenance=Provenance(source_id="x:1", speaker="travel-agent", authority=0.9),
    )
    assert not policy.check(rogue, PRIYA, newest).admitted


def test_the_poisoning_residual_is_real(memories) -> None:
    """Only slot-naming claims are arbitrated; 2 of 3 agent writes are not."""
    from memlab.agents.trust import unchecked

    assert len(unchecked(memories)) == 2


def test_extraction_leaves_the_timestamp_in_four_records(memories) -> None:
    target = next(m for m in memories if "Halloway" in m.content)
    kept = purge(target, memories)
    carrying = [
        m
        for m in kept
        if target.happened_at
        in (m.happened_at, m.valid_from, m.valid_to, m.invalid_at)
    ]
    assert len(carrying) == 4
    assert sum(1 for m in kept if target.id in m.derived_from) == 0, (
        "the cascade had nothing to follow"
    )


def test_the_sharpest_residue_is_a_parser_written_field(memories) -> None:
    """A1 resolved "before the move" from the address memory's timestamp."""
    target = next(m for m in memories if "Halloway" in m.content)
    cycling = next(m for m in memories if "before the move" in m.content)
    assert cycling.valid_from == target.happened_at
    assert target.id not in cycling.derived_from


def test_deleting_both_pii_records_does_not_help(memories) -> None:
    """The stretch: they share a turn, so each records the other's instant."""
    address = next(m for m in memories if "Halloway" in m.content)
    phone = next(m for m in memories if "07700 900412" in m.content)
    assert address.happened_at == phone.happened_at
    kept = purge(phone, purge(address, memories))
    assert any(m.happened_at == address.happened_at for m in kept)
