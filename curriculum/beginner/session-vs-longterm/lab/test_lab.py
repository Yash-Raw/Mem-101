"""Promotion is a decision Beginner makes by default. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.fixtures import load_turns
from memlab.retrieve.embedding import EmbeddingRetriever
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope, Tier

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

would_promote = _solution.would_promote

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def state(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("promo") / "m.jsonl")
    ingest(store, PRIYA)
    turns = {f"s{t['session']}:{t['ts']}": t["text"] for t in load_turns(user_only=True)}
    return store.all(), turns, would_promote(store.all(), turns)


def test_stub_is_runnable(state) -> None:
    memories, _turns, _ = state
    with pytest.raises(NotImplementedError):
        _lab.promotion_tier(memories[0], "")


def test_the_current_system_promotes_everything(state) -> None:
    """Not a decision. The absence of one."""
    memories, _, _ = state
    assert {m.tier for m in memories} == {Tier.WORKING}, "all defaulted, none decided"


def test_the_gate_demotes_six(state) -> None:
    _, _, tiers = state
    assert len(tiers[Tier.LONG_TERM]) == 30
    assert len(tiers[Tier.SCRATCH]) + len(tiers[Tier.WORKING]) == 6


def test_a_request_is_not_a_fact(state) -> None:
    _, _, tiers = state
    scratch = {m.content for m in tiers[Tier.SCRATCH]}
    assert "Priya asked to forget her old address" in scratch


def test_procedures_are_always_promoted(state) -> None:
    from memlab.types import MemoryType

    _, _, tiers = state
    promoted = {m.content for m in tiers[Tier.LONG_TERM]}
    memories, _, _ = state
    for m in memories:
        if m.type is MemoryType.PROCEDURAL:
            assert m.content in promoted


def test_a_demoted_memory_is_occupying_a_top_ten_slot(state) -> None:
    """The argument for the gate, stated at its strongest.

    "Priya completed her first week at the new job" -- true for one week in
    January -- ranks 6th for a question about her employer and her diet. It is
    not merely wasting storage; it is spending one of the ten slots the model
    will ever see.
    """
    memories, _, tiers = state
    demoted = {m.id for m in tiers[Tier.SCRATCH] + tiers[Tier.WORKING]}
    hits = EmbeddingRetriever().search(
        "where do I work and what should I not eat?", memories, PRIYA, k=10
    )
    intruders = [h.memory.content for h in hits if h.memory.id in demoted]
    assert intruders == ["Priya completed her first week at the new job"]


def test_demoting_loses_no_relevant_fact(state) -> None:
    """It frees a slot, and costs nothing the question needed."""
    memories, _, tiers = state
    demoted = {m.id for m in tiers[Tier.SCRATCH] + tiers[Tier.WORKING]}
    kept = [m for m in memories if m.id not in demoted]

    q = "where do I work and what should I not eat?"
    before = EmbeddingRetriever().search(q, memories, PRIYA, k=10)
    after = EmbeddingRetriever().search(q, kept, PRIYA, k=10)

    def relevant(hits):
        text = " ".join(h.memory.content for h in hits)
        return {w for w in ("meat", "gluten", "Northwind", "Calico") if w in text}

    assert relevant(after) >= relevant(before), "nothing the question needed was lost"
    assert {h.memory.id for h in after} - {h.memory.id for h in before}, "and a slot opened up"


def test_a_turn_level_marker_over_protects(state) -> None:
    """The gate's own bug, pinned: 'keep that in mind' shields the Spark job too."""
    _, _, tiers = state
    promoted = {m.content for m in tiers[Tier.LONG_TERM]}
    assert "Priya is debugging a Spark job" in promoted
    assert "Priya is vegetarian" in promoted, "the marker was about this one"
