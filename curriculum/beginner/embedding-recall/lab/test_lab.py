"""Similarity measures aboutness, not agreement. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.llm.fake import cosine, embed_text
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

most_similar_pairs = _solution.most_similar_pairs
search = _solution.search

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("emb") / "m.jsonl")
    ingest(store, PRIYA)
    return store.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.search("x", memories, PRIYA)


def test_search_ranks_and_cuts(memories) -> None:
    hits = search("what should I not eat?", memories, PRIYA, k=4)
    assert len(hits) == 4
    assert [s for s, _ in hits] == sorted((s for s, _ in hits), reverse=True)


def test_scope_is_a_hard_filter_not_a_ranking_signal(memories) -> None:
    """A stranger gets nothing back -- not 'the closest thing we could find'."""
    assert search("what should I not eat?", memories, Scope(user="stranger"), k=5) == []


def test_the_top_pair_is_a_duplicate_the_extractor_made(memories) -> None:
    """Highest similarity in the whole store is one fact recorded twice."""
    score, a, b = most_similar_pairs(memories, top=1)[0]
    joined = f"{a.content} || {b.content}"
    assert "Samira" in joined and "charge nurse" in joined
    assert score > 0.75


def test_one_score_band_holds_five_different_relationships(memories) -> None:
    """The lesson's central claim: the number cannot name the relationship."""
    top = most_similar_pairs(memories, top=8)
    joined = [f"{a.content} || {b.content}" for _, a, b in top]

    def find(x: str, y: str) -> int | None:
        return next((i for i, j in enumerate(joined) if x in j and y in j), None)

    duplicate = find("Samira got a promotion", "Samira is a charge nurse")
    retraction = find("data engineer at Northwind", "leaving Northwind")
    refinement = find("is vegetarian", "is pescatarian")
    contradiction = find("drinks tea", "three coffees")

    assert None not in (duplicate, retraction, refinement, contradiction)
    scores = [top[i][0] for i in (duplicate, retraction, refinement, contradiction)]
    assert max(scores) - min(scores) < 0.25, "four relationships, one narrow score band"


def test_a_duplicate_outscores_a_contradiction(memories) -> None:
    """Score tracks phrasing overlap, not logical interaction."""
    top = most_similar_pairs(memories, top=8)
    joined = [(s, f"{a.content} || {b.content}") for s, a, b in top]
    dup = next(s for s, j in joined if "Samira got a promotion" in j)
    contra = next(s for s, j in joined if "drinks tea" in j and "three coffees" in j)
    assert dup > contra


def test_similarity_cannot_see_negation_either() -> None:
    assert cosine(
        embed_text("Priya does not drink coffee"),
        embed_text("Priya drinks three coffees a day"),
    ) > 0.4


