"""Rules decide, in an order that matters. Asserted."""
from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.evolve.conflict import detect
from memlab.evolve.operations import Operation, decide_all
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Memory, MemoryType, Provenance, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

FIRST_PARTY = _solution.FIRST_PARTY
arbitrate = _solution.arbitrate

PRIYA = Scope(user="priya")


def mem(content: str, when: str, authority: float = 0.9, confidence: float = 0.9) -> Memory:
    return Memory(
        content=content, type=MemoryType.SEMANTIC, scope=PRIYA,
        provenance=Provenance(source_id=f"src:{content[:10]}", speaker="user",
                              authority=authority),
        happened_at=datetime.fromisoformat(when).replace(tzinfo=UTC),
        confidence=confidence,
    )


@pytest.fixture(scope="module")
def verdicts(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("arb") / "m.jsonl")
    ingest(store, PRIYA, at("I3"))
    return [
        d.verdict for d in decide_all(detect(store.all(), PRIYA))
        if d.operation is Operation.UPDATE and d.verdict
    ]


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.arbitrate(mem("a", "2025-01-01"), mem("b", "2026-01-01"))


def test_authority_beats_recency() -> None:
    """The Berlin case, isolated. Newer AND relayed must still lose."""
    address = mem("Priya lives at 47 Halloway Road", "2025-08-02", authority=0.9)
    hearsay = mem("colleague mentioned relocating to Berlin", "2026-05-16", authority=0.3)
    v = arbitrate(address, hearsay)
    assert v.winner is address
    assert v.rule == "authority"


def test_recency_uses_event_time_not_ingestion() -> None:
    """Both facts arrive in one turn; only event time separates them."""
    cycled = mem("Priya cycles to work", "2025-01-01")
    train = mem("Priya commutes 40 minutes by train", "2025-09-01")
    assert arbitrate(cycled, train).winner is train


def test_confidence_breaks_a_tie_within_one_moment() -> None:
    a = mem("claim a", "2026-01-01", confidence=0.9)
    b = mem("claim b", "2026-01-01", confidence=0.5)
    v = arbitrate(a, b)
    assert v.winner is a and v.rule == "confidence"


def test_the_tiebreak_is_stable_not_random() -> None:
    a = mem("claim a", "2026-01-01")
    b = mem("claim b", "2026-01-01")
    first = arbitrate(a, b)
    assert first.rule == "stable-tiebreak"
    assert all(arbitrate(a, b).winner.id == first.winner.id for _ in range(5))
    assert arbitrate(b, a).winner.id == first.winner.id, "order-independent"


def test_the_corpus_resolves_seven_on_recency_and_one_on_authority(verdicts) -> None:
    assert Counter(v.rule for v in verdicts) == {"recency": 7, "authority": 1}


def test_the_hearsay_is_the_one_decided_on_authority(verdicts) -> None:
    by_authority = [v for v in verdicts if v.rule == "authority"]
    assert len(by_authority) == 1
    assert "Berlin" in by_authority[0].loser.content
    assert by_authority[0].loser.provenance.authority < FIRST_PARTY


def test_every_verdict_names_its_rule(verdicts) -> None:
    assert all(v.rule and v.reason for v in verdicts)
