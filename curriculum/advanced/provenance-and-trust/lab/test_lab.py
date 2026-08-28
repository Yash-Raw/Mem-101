"""Trust the claim, not the claimant -- and flag what cannot be assessed."""
from __future__ import annotations

from collections import Counter

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

COMPETENCE = _solution.COMPETENCE
Verdict = _solution.Verdict
assess = _solution.assess
unchecked = _solution.unchecked

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("pt") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    return s.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.assess(memories[0])


def test_two_of_three_agent_writes_are_never_arbitrated(memories) -> None:
    """"Nothing disagreed" and "nothing looked" are the same output."""
    agent_writes = [m for m in memories if m.scope.agent]
    assert len(agent_writes) == 3
    missed = unchecked(memories)
    assert len(missed) == 2
    assert all(m.provenance.speaker == "calendar-agent" for m in missed)


def test_the_one_that_is_checked_is_checked_by_accident(memories) -> None:
    """It happened to claim a slot the user also claims."""
    rumour = next(m for m in memories if "relocating to Berlin" in m.content)
    a = assess(rumour)
    assert a.slot == "residence"
    assert a.verdict is Verdict.OUT_OF_DOMAIN
    assert a.trust == 0.3
    assert a.checkable


def test_an_unnameable_claim_keeps_its_authority(memories) -> None:
    """The gap is in the vocabulary, not in the writer."""
    for m in unchecked(memories):
        a = assess(m)
        assert a.verdict is Verdict.UNNAMEABLE
        assert a.trust == m.provenance.authority == 0.9
        assert not a.checkable


def test_a_two_state_policy_punishes_the_reliable_writer(memories) -> None:
    """The stretch, asserted: collapse the verdicts and the rumour is untouched."""
    def two_state(m):
        a = assess(m)
        within = a.slot is not None and a.slot in COMPETENCE.get(
            m.provenance.speaker, frozenset()
        )
        return m.provenance.authority if within else 0.3

    calendar = [m for m in memories if m.provenance.speaker == "calendar-agent"]
    rumour = next(m for m in memories if "relocating to Berlin" in m.content)
    assert [assess(m).trust for m in calendar] == [0.9, 0.9]
    assert [two_state(m) for m in calendar] == [0.3, 0.3]
    assert assess(rumour).trust == two_state(rumour) == 0.3


def test_the_store_wide_split(memories) -> None:
    counts = Counter(assess(m).verdict.value for m in memories)
    assert counts["competent"] == 27
    assert counts["unnameable"] == 9
    assert counts["out of domain"] == 1
    assert sum(counts.values()) == 37


def test_the_vocabulary_gap_is_not_an_agent_problem(memories) -> None:
    users_own = [
        m
        for m in memories
        if m.provenance.speaker == "user" and assess(m).verdict is Verdict.UNNAMEABLE
    ]
    assert len(users_own) == 7


def test_the_calendar_competence_entry_never_fires(memories) -> None:
    """Kept because it is correct, not because it earns anything here."""
    assert COMPETENCE["calendar-agent"] == frozenset({"commute"})
    consulted = {
        assess(m).slot
        for m in memories
        if m.scope.agent and assess(m).verdict is not Verdict.UNNAMEABLE
    }
    assert consulted == {"residence"}


def test_a_relay_is_authoritative_about_nothing(memories) -> None:
    assert COMPETENCE["travel-agent"] == frozenset()
