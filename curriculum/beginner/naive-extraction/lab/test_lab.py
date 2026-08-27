"""Extraction quality caps retrieval quality. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.extract.naive import extract
from memlab.fixtures import load_gold, load_turns, session
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

audit_against_gold = _solution.audit_against_gold
type_histogram = _solution.type_histogram

SCOPE = Scope(user="priya")


@pytest.fixture(scope="module")
def memories():
    out = []
    for turn in load_turns(user_only=True):
        if turn["session"] < 14:
            out.extend(extract(turn, SCOPE))
    return out


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.audit_against_gold(memories, load_gold())


def test_extraction_produces_a_plausible_store(memories) -> None:
    """It looks fine. That is the problem."""
    assert len(memories) == 36
    assert type_histogram(memories) == {
        "semantic": 22, "episodic": 12, "procedural": 2, "working": 0
    }


def test_atomicity_where_it_helps(memories) -> None:
    """Session 7's one sentence becomes three independently updatable facts."""
    s7 = [m.content for m in extract(next(t for t in session(7)), SCOPE)]
    assert len(s7) == 3
    assert all(len(c.split()) < 8 for c in s7), "each stands alone"


def test_atomicity_correctly_broken_for_a_procedure(memories) -> None:
    """Order is load-bearing, so the procedure stays whole."""
    procs = [m for m in memories if m.type is MemoryType.PROCEDURAL]
    steps = next(m for m in procs if "warehouse" in m.content)
    for step in ("pull pipeline metrics", "diff against last week", "15% drift"):
        assert step in steps.content, "splitting this would destroy the ordering"


def test_the_employer_state_was_never_created(memories) -> None:
    """The headline failure, found by auditing for an ABSENCE."""
    findings = audit_against_gold(memories, load_gold())
    assert "missing_state" in findings
    assert not any("works at Calico" in m.content for m in memories)


def test_the_event_state_split_is_phrasing_dependent(memories) -> None:
    """Same extractor: session 8 yields only events, session 12 yields a state."""
    s8 = extract(next(t for t in session(8)), SCOPE)
    s12 = extract(next(t for t in session(12)), SCOPE)
    assert {m.type for m in s8} == {MemoryType.EPISODIC}
    assert MemoryType.SEMANTIC in {m.type for m in s12}


def test_pii_and_deletion_failures_are_already_present(memories) -> None:
    findings = audit_against_gold(memories, load_gold())
    assert "ungated_pii" in findings
    assert "unhonoured_deletion" in findings
