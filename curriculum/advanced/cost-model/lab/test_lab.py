"""Every model call happens while nobody is waiting."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ask, ingest
from memlab.eval.exam import QUESTION
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Cost = _solution.Cost
counting = _solution.counting
ratio = _solution.ratio

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def paths(tmp_path_factory):
    pipeline = at("A3")
    store = JsonlStore(tmp_path_factory.mktemp("cm") / "m.jsonl")
    with counting() as counts:
        store.clear()
        ingest(store, PRIYA, pipeline)
    write = Cost(**counts)

    pipeline.vectors.index(store.all())
    with counting() as counts:
        ask(store, PRIYA, QUESTION, k=5, pipeline=pipeline)
    return write, Cost(**counts), store, pipeline


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError), _lab.counting():
        pass


def test_the_read_path_makes_no_model_calls(paths) -> None:
    _write, read, _s, _p = paths
    assert read.llm == 0
    assert read.embed == 2


def test_the_write_path_costs_forty_eight_calls(paths) -> None:
    write, _read, _s, _p = paths
    assert (write.llm, write.embed) == (48, 38)


def test_two_model_calls_per_turn(paths) -> None:
    """Linear in messages, independent of how much has been remembered."""
    write, _read, _s, _p = paths
    assert write.per(24) == (2.0, 1.6)


def test_the_ratio_reports_the_division_by_zero(paths) -> None:
    write, read, _s, _p = paths
    assert ratio(write, read) == ("no model calls at all", "19x")


def test_a_name_imported_before_the_patch_is_not_counted() -> None:
    """`from x import y` copies a reference; the patch cannot reach it.

    This is the limitation the `_IMPORTERS` list exists for, and it is the
    reason the list has to be maintained rather than derived.
    """
    from memlab.llm import fake
    from memlab.llm.fake import embed_text as bound_early

    with counting() as counts:
        fake.embed_text("through the module")
        bound_early("through a copied reference")
    assert counts["embed"] == 1


def test_every_importer_is_patched() -> None:
    """Stops `_IMPORTERS` going stale as modules are added."""
    import pathlib as _pathlib

    import memlab

    root = _pathlib.Path(memlab.__file__).parent
    importers = {
        "memlab."
        + str(path.relative_to(root)).removesuffix(".py").replace("/", ".")
        for path in root.rglob("*.py")
        if "import embed_text" in path.read_text()
        or "cosine, embed_text" in path.read_text()
    }
    importers = {
        m
        for m in importers
        if not m.startswith("memlab.llm") and m != "memlab.cost.profile"
    }
    assert importers == set(_solution._IMPORTERS)


def test_counting_restores_the_originals() -> None:
    from memlab.llm import fake

    before = fake.embed_text
    with counting():
        pass
    assert fake.embed_text is before


def test_the_embedding_cost_moves_and_the_model_cost_does_not(tmp_path) -> None:
    """The stretch: the read is cheap only because the write path paid.

    Index everything first and the read pays 2 -- the query, plus one memory
    the index had not reached. Skip indexing and it pays 20, embedding on
    demand exactly as I7's 2N-per-query behaviour did. What does not move in
    either configuration is the model cost.
    """
    results = {}
    for indexed in (True, False):
        pipeline = at("A3")
        store = JsonlStore(tmp_path / f"warm-{indexed}.jsonl")
        store.clear()
        ingest(store, PRIYA, pipeline)
        if indexed:
            pipeline.vectors.index(store.all())
        with counting() as counts:
            ask(store, PRIYA, QUESTION, k=5, pipeline=pipeline)
        results[indexed] = (len(pipeline.vectors.vectors), dict(counts))

    assert results[True] == (37, {"llm": 0, "embed": 2})
    assert results[False] == (18, {"llm": 0, "embed": 20})
    assert all(r[1]["llm"] == 0 for r in results.values())
