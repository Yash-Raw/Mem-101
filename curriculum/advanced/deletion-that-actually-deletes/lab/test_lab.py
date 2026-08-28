"""The seventh failure, closed -- and the ambiguity that must not be."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.privacy.classify import Kind
from memlab.store.jsonl import JsonlStore
from memlab.store.sqlite import SqliteStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Request = _solution.Request
cascade = _solution.cascade
purge = _solution.purge
resolve = _solution.resolve

PRIYA = Scope(user="priya")
REQUEST = Request(
    text="forget my old address, I don't want that stored anywhere",
    session=13,
    at=datetime(2026, 6, 20, tzinfo=UTC),
)


@pytest.fixture
def built(tmp_path):
    pipeline = at("A3")
    store = JsonlStore(tmp_path / "m.jsonl")
    store.clear()
    ingest(store, PRIYA, pipeline)
    memories = store.all()
    pipeline.vectors.index(memories)
    sqlite = SqliteStore(tmp_path / "m.db")
    sqlite.clear()
    sqlite.add(memories)
    return memories, pipeline, sqlite


def test_stub_is_runnable(built) -> None:
    memories, _p, _s = built
    with pytest.raises(NotImplementedError):
        _lab.resolve(REQUEST, memories, Kind.ADDRESS)


def test_the_users_word_is_not_the_stores_word(built) -> None:
    """Searching for "address" returns nothing; the request looks satisfied."""
    memories, _p, _s = built
    assert sum(1 for m in memories if "address" in m.content.lower()) == 0
    assert any("lives at 47 Halloway Road" in m.content for m in memories)


def test_the_label_resolves_it(built) -> None:
    memories, _p, _s = built
    found = resolve(REQUEST, memories, Kind.ADDRESS)
    assert len(found.candidates) == 1
    assert "47 Halloway Road" in found.candidates[0].content


def test_actionable_is_not_unambiguous(built) -> None:
    """One candidate, and the reason is why a system must not act on it."""
    memories, _p, _s = built
    found = resolve(REQUEST, memories, Kind.ADDRESS)
    assert found.actionable
    assert "'old'" in found.reason
    assert found.candidates[0].provenance.source_id.startswith("s5:")


def test_the_old_address_was_never_stored(built) -> None:
    from memlab.fixtures import load_turns

    said = next(t["text"] for t in load_turns() if t["session"] == 5 and "moved" in t["text"])
    assert "New place is 47 Halloway Road" in said
    memories, _p, _s = built
    addresses = [m for m in memories if "Road" in m.content or "Street" in m.content]
    assert len(addresses) == 1, "only ever the new one"


def test_the_cascade_reaches_three_structures(built) -> None:
    memories, pipeline, sqlite = built
    target = next(m for m in memories if "Halloway" in m.content)
    assert pipeline.vectors.holds(target.id)

    result = cascade(target, memories, pipeline.vectors, sqlite)
    kept = purge(target, memories)

    assert (result.primary, result.sqlite, result.vectors) == (1, 1, 1)
    assert result.total == 3
    assert not any("Halloway" in m.content for m in kept)
    assert not any("Halloway" in m.content for m in sqlite.all())
    assert not pipeline.vectors.holds(target.id)


def test_the_zeroes_are_reported(built) -> None:
    """A cascade printing only non-zero counts looks the same as one that
    never walked the graph."""
    memories, pipeline, sqlite = built
    target = next(m for m in memories if "Halloway" in m.content)
    result = cascade(target, memories, pipeline.vectors, sqlite)
    assert result.derived == 0
    assert result.summaries == 0


def test_forget_destroys_where_tombstoning_keeps(built) -> None:
    """index() keeps a retired belief's vector on purpose. Deletion inverts it."""
    memories, pipeline, _s = built
    retired = next(m for m in memories if not m.is_live)
    assert pipeline.vectors.holds(retired.id), "tombstoned, and the vector kept"
    assert retired.id in pipeline.vectors.tombstoned

    assert pipeline.vectors.forget(retired.id)
    assert not pipeline.vectors.holds(retired.id)
    assert retired.id not in pipeline.vectors.tombstoned


def test_holds_does_not_create_what_it_looks_for(built) -> None:
    """The stretch: `vector_for` computes one, and would recreate the deletion."""
    memories, pipeline, _s = built
    target = next(m for m in memories if "Halloway" in m.content)
    pipeline.vectors.forget(target.id)
    assert not pipeline.vectors.holds(target.id)
    size = len(pipeline.vectors.vectors)
    assert not pipeline.vectors.holds(target.id)
    assert len(pipeline.vectors.vectors) == size

    pipeline.vectors.vector_for(target)
    assert len(pipeline.vectors.vectors) == size + 1, "computed the deleted vector"


def test_purge_takes_derived_records_with_it(built) -> None:
    from dataclasses import replace as dc_replace

    memories, _p, _s = built
    target = next(m for m in memories if "Halloway" in m.content)
    derived = dc_replace(
        target, content="a summary citing the address", derived_from=(target.id,), id=""
    )
    kept = purge(target, [*memories, derived])
    assert target.id not in {m.id for m in kept}
    assert derived.id not in {m.id for m in kept}
