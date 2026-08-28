"""Eight times the store, a hundred and four times the pairs."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

measure = _solution.measure
partition_key = _solution.partition_key
replicate = _solution.replicate

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("sc") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    return s.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.replicate(memories, 2)


@pytest.mark.parametrize(
    "factor,mem,eligible,pairs",
    [(1, 37, 18, 9), (2, 74, 36, 49), (4, 148, 72, 222), (8, 296, 144, 940)],
)
def test_the_growth_curve(memories, factor, mem, eligible, pairs) -> None:
    growth = measure(memories, PRIYA, factor)
    assert (growth.memories, growth.eligible, growth.pairs) == (mem, eligible, pairs)


def test_retrieval_grows_linearly_and_consolidation_does_not(memories) -> None:
    one, eight = measure(memories, PRIYA, 1), measure(memories, PRIYA, 8)
    assert eight.memories // one.memories == 8
    assert eight.eligible // one.eligible == 8
    assert eight.pairs // one.pairs == 104


def test_pairs_per_memory_climbs(memories) -> None:
    """Blocking bounds the number of groups, not the size of one."""
    rates = [measure(memories, PRIYA, f).per_memory_pairs for f in (1, 2, 4, 8)]
    assert rates == [0.2, 0.7, 1.5, 3.2]
    assert rates == sorted(rates)


def test_replication_without_distinct_ids_measures_nothing(memories) -> None:
    """The stretch: content-addressed ids collapse the copies."""
    naive = [*memories, *memories, *memories]
    assert len({m.id for m in naive}) == len(memories)
    assert len({m.id for m in replicate(memories, 3)}) == len(memories) * 3


def test_replication_preserves_content(memories) -> None:
    """Only the size varies; the distribution is held fixed."""
    grown = replicate(memories, 4)
    assert sorted({m.content for m in grown}) == sorted({m.content for m in memories})


def test_the_tier_cap_is_per_store(memories) -> None:
    """Eight replicated stores are eight caps, so it does not bind here."""
    from memlab.forget.budget import DEFAULT_CAP

    assert DEFAULT_CAP == 20
    assert measure(memories, PRIYA, 8).eligible > DEFAULT_CAP


def test_the_partition_key_is_the_correctness_boundary() -> None:
    key = partition_key()
    assert key.startswith("user")
    assert "correctness boundary" in key


def test_scopes_really_partitions_on_user(memories) -> None:
    from memlab.store.scopes import partition

    assert all(k.split("/")[0] == "priya" for k in partition(memories))
