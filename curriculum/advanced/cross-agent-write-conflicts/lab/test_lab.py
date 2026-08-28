"""A threshold, not a slope -- and what sits one notch above it."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from memlab import labkit
from memlab.app.chat import _agent_memories, ingest
from memlab.fixtures import load_turns
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Memory, MemoryType, Provenance, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

above_the_line = _solution.above_the_line
cross_writer = _solution.cross_writer
decided_by = _solution.decided_by

PRIYA = Scope(user="priya")
OLD, NEW = datetime(2025, 8, 2, tzinfo=UTC), datetime(2026, 6, 1, tzinfo=UTC)


def _memory(content, speaker, authority, when, agent=None):
    return Memory(
        content=content,
        type=MemoryType.SEMANTIC,
        scope=Scope(user="priya", agent=agent),
        happened_at=when,
        provenance=Provenance(
            source_id=f"{speaker}:x", speaker=speaker, authority=authority
        ),
        confidence=authority,
    )


@pytest.fixture(scope="module")
def raw():
    """Unconsolidated: reconciliation retires losers, and losers are not
    candidates. Measuring after it returns zero for the wrong reason."""
    pipeline = at("A3")
    return [
        m
        for turn in load_turns(user_only=True)
        if turn["session"] < 14
        for m in pipeline.extract(turn, PRIYA)
    ] + _agent_memories(PRIYA)


def test_stub_is_runnable(raw) -> None:
    with pytest.raises(NotImplementedError):
        _lab.cross_writer(raw, PRIYA)


def test_the_corpus_has_exactly_one_cross_writer_conflict(raw) -> None:
    pairs = cross_writer(raw, PRIYA)
    assert len(pairs) == 1
    assert pairs[0].slot == "residence"
    assert set(pairs[0].writers) == {"user", "travel-agent"}
    assert not pairs[0].agent_versus_agent


def test_and_zero_agent_versus_agent(raw) -> None:
    """The two agents claim disjoint slots. Reported, not simulated."""
    assert [p for p in cross_writer(raw, PRIYA) if p.agent_versus_agent] == []


def test_measuring_after_consolidation_returns_zero(tmp_path) -> None:
    """A clean number describing your timing rather than your corpus."""
    store = JsonlStore(tmp_path / "after.jsonl")
    store.clear()
    ingest(store, PRIYA, at("A3"))
    assert cross_writer(store.all(), PRIYA) == []


def test_a_relay_loses_on_authority_either_way() -> None:
    mine = _memory("Priya is pescatarian", "user", 1.0, OLD)
    relay = _memory(
        "Priya's colleague mentioned she is relocating",
        "travel-agent", 0.3, NEW, "travel-agent",
    )
    assert not above_the_line(relay)
    assert decided_by(mine, relay) == ("authority", "user", "authority", "user")


def test_an_agent_above_the_line_wins_on_recency() -> None:
    """0.9 and 1.0 are the same number to a threshold at 0.5."""
    mine = _memory("Priya is pescatarian", "user", 1.0, OLD)
    agent = _memory("Priya is vegetarian", "calendar-agent", 0.9, NEW, "calendar-agent")
    assert above_the_line(agent)
    rule_a, winner_a, rule_t, winner_t = decided_by(mine, agent)
    assert (rule_a, winner_a) == ("recency", "calendar-agent")
    assert (rule_t, winner_t) == ("authority", "user")


def test_trust_changes_no_outcome_on_this_corpus(tmp_path) -> None:
    """@A3 == @A2. The mechanism is unproven on this data, not unnecessary."""
    a2 = JsonlStore(tmp_path / "a2.jsonl")
    a2.clear()
    ingest(a2, PRIYA, at("A2"))
    a3 = JsonlStore(tmp_path / "a3.jsonl")
    a3.clear()
    ingest(a3, PRIYA, at("A3"))
    assert [(m.id, m.invalid_at) for m in a2.all()] == [
        (m.id, m.invalid_at) for m in a3.all()
    ]


def test_the_defence_is_one_constant_away(raw) -> None:
    """The stretch: raise the relay above the line and the address loses."""
    from dataclasses import replace as dc_replace

    mine = next(m for m in raw if "47 Halloway Road" in m.content)
    relay = next(m for m in raw if "relocating to Berlin" in m.content)
    assert decided_by(mine, relay)[1] == "user"

    promoted = dc_replace(
        relay, provenance=dc_replace(relay.provenance, authority=0.6), confidence=0.6
    )
    rule, winner, _rt, _wt = decided_by(mine, promoted)
    assert (rule, winner) == ("recency", "travel-agent")
