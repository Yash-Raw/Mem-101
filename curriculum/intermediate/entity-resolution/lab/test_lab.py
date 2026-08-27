"""Resolution needs the whole store. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import get
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

block_key = _solution.block_key
cluster = _solution.cluster
resolve_all = _solution.resolve_all
resolve_incrementally = _solution.resolve_incrementally
score = _solution.score

PARTNER = ("Sam ", "Sam's", "Samira", "Sammy")


@pytest.fixture(scope="module")
def about_partner(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("res") / "m.jsonl")
    ingest(store, Scope(user="priya"), get("intermediate"))
    return [
        m for m in store.all()
        if any(n in m.content for n in PARTNER) or m.content.startswith("She")
    ]


def test_stub_is_runnable() -> None:
    with pytest.raises(NotImplementedError):
        _lab.score("Sam", "Samira")


def test_blocking_groups_the_variants() -> None:
    assert block_key("Sam") == block_key("Samira") == block_key("Sammy") == "sam"
    assert block_key("Priya") != block_key("Sam")


def test_the_score_gap_is_wide(monkeypatch) -> None:
    """The threshold is not doing the work -- the separation is."""
    within = min(score("Sam", "Samira"), score("Sam", "Sammy"), score("Samira", "Sammy"))
    across = score("Sam", "Priya")
    assert within >= 0.7 and across <= 0.3
    assert within - across > 0.4


def test_the_cluster_picks_the_longest_name(monkeypatch) -> None:
    assignments = cluster({"Sam", "Samira", "Sammy", "Priya"})
    assert assignments["Sam"] == assignments["Samira"] == assignments["Sammy"] == "samira"
    assert assignments["Priya"] == "priya"


def test_store_wide_resolution_yields_one_identity(about_partner) -> None:
    ids = {e for m in resolve_all(about_partner) for e in m.entities}
    assert ids == {"samira"}
    assert len(about_partner) == 6


def test_the_bare_pronoun_resolves_too(about_partner) -> None:
    resolved = resolve_all(about_partner)
    pronoun = next(m for m in resolved if m.content.startswith("She works nights"))
    assert pronoun.entities == ("samira",)


def test_incremental_resolution_gives_one_person_two_ids(about_partner) -> None:
    """The finding this lesson is built on."""
    ids = {e for m in resolve_incrementally(about_partner) for e in m.entities}
    assert len(ids) > 1, "resolving before the evidence arrives is unstable"
    assert ids > {"samira"} or "sam" in ids


def test_resolution_links_and_never_rewrites(about_partner) -> None:
    before = [m.content for m in about_partner]
    after = [m.content for m in resolve_all(about_partner)]
    assert before == after, "content must be byte-identical"


def test_resolution_is_idempotent(about_partner) -> None:
    once = resolve_all(about_partner)
    twice = resolve_all(once)
    assert [(m.id, m.entities) for m in once] == [(m.id, m.entities) for m in twice]
