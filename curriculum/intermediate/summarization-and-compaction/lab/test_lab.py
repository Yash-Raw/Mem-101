"""Compression comes from what you drop. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import get
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

orphaned_summaries = _solution.orphaned_summaries
summarise_all = _solution.summarise_all
summarise_session = _solution.summarise_session

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("sum") / "m.jsonl")
    ingest(store, PRIYA, get("intermediate"))
    return store.all()


@pytest.fixture(scope="module")
def summaries(memories):
    return summarise_all(memories, PRIYA)


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.summarise_session(memories, "s1", PRIYA)


def test_every_summary_records_its_sources(summaries) -> None:
    """The field that makes a summary rebuildable and deletable."""
    for s in summaries:
        assert s.memory.derived_from
        assert set(s.memory.derived_from) == {m.id for m in s.sources}


def test_some_sessions_expand(summaries) -> None:
    """An extractive summary that drops nothing is not a compression."""
    expanded = [s for s in summaries if s.compression > 1.0]
    assert expanded, "sessions with no episodes to drop get bigger"
    for s in expanded:
        assert s.dropped == 0, "nothing was dropped, so nothing was gained"


def test_compression_tracks_what_was_dropped(summaries) -> None:
    for s in summaries:
        assert (s.compression < 1.0) == (s.dropped > 0)


def test_the_whole_store_compresses_modestly(memories, summaries) -> None:
    before = sum(len(m.content) for m in memories)
    after = sum(len(s.memory.content) for s in summaries)
    assert 0.7 < after / before < 0.9


def test_episodes_are_never_summarised(summaries) -> None:
    """Their timestamps are the thing that makes them worth keeping."""
    for s in summaries:
        assert all(m.type is not MemoryType.EPISODIC for m in s.sources)


def test_every_claim_is_verbatim_from_a_source(summaries) -> None:
    """Extractive means nothing can be invented."""
    for s in summaries:
        for source in s.sources:
            assert source.content in s.memory.content


def test_deleting_a_source_orphans_its_summary(memories, summaries) -> None:
    victim = summaries[0].sources[0]
    survivors = [m for m in memories if m.id != victim.id] + [s.memory for s in summaries]
    orphans = orphaned_summaries(survivors)
    assert len(orphans) == 1
    assert victim.id in orphans[0].derived_from


def test_an_intact_store_has_no_orphans(memories, summaries) -> None:
    assert orphaned_summaries(memories + [s.memory for s in summaries]) == []
