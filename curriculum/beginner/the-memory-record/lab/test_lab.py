"""Retirement preserves history. Asserted."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from memlab import labkit
from memlab.types import Memory, MemoryType, Provenance, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

as_of = _solution.as_of
supersede = _solution.supersede

SCOPE = Scope(user="priya")


def mem(content: str, happened: str) -> Memory:
    return Memory(
        content=content, type=MemoryType.SEMANTIC, scope=SCOPE,
        provenance=Provenance(source_id=f"src:{content[:8]}", speaker="user"),
        happened_at=datetime.fromisoformat(happened).replace(tzinfo=UTC),
    )


@pytest.fixture
def store() -> list[Memory]:
    old = mem("Priya works at Northwind Labs", "2025-03-04")
    new = mem("Priya works at Calico Systems", "2026-01-01")
    retired, current = supersede(old, new, at=datetime(2026, 1, 1, tzinfo=UTC))
    return [retired, current]


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.supersede(mem("a", "2025-01-01"), mem("b", "2026-01-01"), datetime.now(UTC))


def test_nothing_is_destroyed(store) -> None:
    assert len(store) == 2
    assert any("Northwind" in m.content for m in store)


def test_the_retired_record_points_at_its_replacement(store) -> None:
    retired = next(m for m in store if "Northwind" in m.content)
    current = next(m for m in store if "Calico" in m.content)
    assert not retired.is_live
    assert retired.superseded_by == current.id
    assert current.is_live


def test_as_of_answers_both_questions(store) -> None:
    """The whole point: both answers are correct, at different times."""
    past = as_of(store, datetime(2025, 6, 1, tzinfo=UTC))
    now = as_of(store, datetime(2026, 6, 1, tzinfo=UTC))
    assert [m.content for m in past] == ["Priya works at Northwind Labs"]
    assert [m.content for m in now] == ["Priya works at Calico Systems"]


def test_a_fact_is_not_live_before_it_became_true(store) -> None:
    """`happened_at` gates the future, not just the past."""
    assert as_of(store, datetime(2025, 1, 1, tzinfo=UTC)) == []


def test_deleting_instead_would_lose_the_answer(store) -> None:
    """Contrast: the same query against a store that deleted on change."""
    deleted = [m for m in store if m.is_live]
    assert as_of(deleted, datetime(2025, 6, 1, tzinfo=UTC)) == [], (
        "with deletion, 'where did I work in 2025' is unanswerable forever"
    )
