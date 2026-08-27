"""Most of the read path is a WHERE clause. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

SqliteStore = _solution.SqliteStore
compare_with_python = _solution.compare_with_python
eligible_sql = _solution.eligible_sql
query_plan = _solution.query_plan

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("sq") / "m.jsonl")
    ingest(store, PRIYA, at("I6"))
    return store.all()


@pytest.fixture
def db(memories):
    store = SqliteStore()
    store.add(memories)
    return store


def test_stub_is_runnable(db) -> None:
    with pytest.raises(NotImplementedError):
        _lab.eligible_sql(db, PRIYA)


def test_it_implements_the_same_interface(db) -> None:
    """Swappable with JsonlStore, not a parallel universe."""
    for method in ("add", "all", "live", "replace", "clear"):
        assert callable(getattr(db, method))
    assert (len(db.all()), len(db.live())) == (37, 30)


def test_inserts_are_idempotent(db, memories) -> None:
    """A content-addressed primary key makes it structural, not remembered."""
    assert db.add(memories) == 0
    assert len(db.all()) == 37


def test_the_query_returns_what_python_filtered(db, memories) -> None:
    result = compare_with_python(db, memories, PRIYA)
    assert result["same_result"]
    assert result["kept"] == 18


def test_and_touches_half_as_many_rows(db, memories) -> None:
    result = compare_with_python(db, memories, PRIYA)
    assert result["sql_rows_returned"] == 18
    assert result["python_rows_loaded"] == 37


def test_the_filters_use_an_index(db) -> None:
    """The plan is the signal; timing will not show anything at this size."""
    plan = " ".join(query_plan(db, PRIYA))
    assert "USING INDEX" in plan
    assert "SCAN" not in plan


def test_exact_terms_are_findable(db) -> None:
    """Including the episodic one similarity ranks poorly."""
    found = {m.content for m in db.search_text("Calico", PRIYA)}
    assert "Priya works at Calico Systems" in found
    assert any("starting at Calico" in c for c in found)


def test_the_namespace_predicate_works(db) -> None:
    """Asserted over ALL rows, because validity already hides the case.

    The travel agent's only memory -- the Berlin hearsay -- was retired by
    arbitration in I4, so among LIVE rows agent scoping narrows nothing. The
    predicate is still correct; the corpus simply removed its subject first.
    """
    rows = db.db.execute(
        "SELECT content FROM memories WHERE user = ? AND (agent IS NULL OR agent = ?)",
        ["priya", "calendar-agent"],
    ).fetchall()
    contents = {r["content"] for r in rows}
    assert not any("Berlin" in c for c in contents), "travel-agent namespace excluded"
    assert any("1:1" in c for c in contents), "calendar-agent namespace included"


def test_agent_scoping_is_moot_among_live_rows(db) -> None:
    everyone = eligible_sql(db, PRIYA, retrievable_only=False)
    calendar = eligible_sql(db, Scope(user="priya", agent="calendar-agent"),
                            retrievable_only=False)
    assert len(everyone) == len(calendar) == 30, (
        "the only foreign-namespace memory is already retired"
    )


def test_a_stranger_gets_nothing(db) -> None:
    assert eligible_sql(db, Scope(user="someone-else")) == []


def test_round_trip_preserves_every_field(db, memories) -> None:
    by_id = {m.id: m for m in db.all()}
    for original in memories:
        restored = by_id[original.id]
        assert (restored.content, restored.type, restored.tier) == (
            original.content, original.type, original.tier
        )
        assert restored.entities == original.entities
        assert restored.invalid_at == original.invalid_at
        assert restored.salience == original.salience
