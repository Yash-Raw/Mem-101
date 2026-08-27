"""Price every element, including the ones that are not memories. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ask, ingest
from memlab.assemble.simple import HEADER, estimate_tokens
from memlab.eval.exam import QUESTION, exam_from_context
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

COMPACT_HEADER = _solution.COMPACT_HEADER
audit = _solution.audit
floor_for = _solution.floor_for

NEEDED = ("works at Calico", "does not eat meat", "eats fish", "gluten")
PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def hits(tmp_path_factory):
    pipeline = at("I7")
    store = JsonlStore(tmp_path_factory.mktemp("sv") / "m.jsonl")
    ingest(store, PRIYA, pipeline)
    pipeline.vectors.index(store.all())
    _ctx, hits = ask(store, PRIYA, QUESTION, k=5, pipeline=pipeline)
    return hits


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("sv2") / "m.jsonl")
    ingest(s, PRIYA, at("I8"))
    return s


def test_stub_is_runnable(hits) -> None:
    with pytest.raises(NotImplementedError):
        _lab.audit(hits)


def test_the_header_is_the_largest_single_element(hits) -> None:
    """Every policy before this one optimised the other 62%."""
    costs = audit(hits, HEADER, precision="dated")
    header = costs[0]
    assert header.element == "header"
    assert header.tokens == 29
    assert round(header.share, 2) == 0.38
    assert header.tokens > max(c.tokens for c in costs[1:])


def test_shares_are_of_the_77_tokens_the_audit_prices(hits) -> None:
    """The assembled string is 80; the priced elements come to 77.

    The three-token difference is the line prefixes the audit does not
    attribute to any element. Shares are of what is priced.
    """
    costs = audit(hits, HEADER, precision="dated")
    assert sum(c.tokens for c in costs) == 77
    assert abs(sum(c.share for c in costs) - 1.0) < 1e-9


def test_the_compact_header_keeps_the_framing(hits) -> None:
    """Right-sized, not removed -- the reliability was never the thing to trade."""
    assert estimate_tokens(COMPACT_HEADER) == 11
    assert estimate_tokens(HEADER) - estimate_tokens(COMPACT_HEADER) == 18, (
        "18 tokens -- one more fact"
    )
    assert "Recalled" in COMPACT_HEADER
    assert "out of date" in COMPACT_HEADER


def test_the_exam_survives_52_tokens(store) -> None:
    for budget in (80, 67, 60, 55, 52):
        assert exam_from_context(
            store.all(), PRIYA, k=5, pipeline=at("I8"), budget=budget
        ).is_correct, f"should pass at {budget}"


def test_and_fails_below_it(store) -> None:
    for budget in (50, 45, 43):
        assert not exam_from_context(
            store.all(), PRIYA, k=5, pipeline=at("I8"), budget=budget
        ).is_correct


def test_it_was_failing_at_67_before(store) -> None:
    assert not exam_from_context(
        store.all(), PRIYA, k=5, pipeline=at("I7"), budget=67
    ).is_correct


def test_the_floor_is_below_what_is_reached(hits) -> None:
    """43 in principle, 52 by any policy here. The gap is one memory."""
    needed = [h for h in hits if any(n in h.memory.content for n in NEEDED)]
    assert floor_for(needed, COMPACT_HEADER) == 43


def test_the_gap_is_a_memory_nothing_can_reject(hits) -> None:
    padding = next(h for h in hits if "staff engineer" in h.memory.content)
    diet = [h for h in hits if any(n in h.memory.content for n in ("eats fish", "gluten"))]
    assert min(h.score for h in diet) < padding.score < max(h.score for h in diet), (
        "a real second answer, scored between the two facts that matter"
    )


def test_element_cost_is_a_ratio(hits) -> None:
    """The same header is 38% at k=5 and far less at k=20."""
    narrow = audit(hits[:5], HEADER, precision="dated")[0].share
    wide = audit(hits * 4, HEADER, precision="dated")[0].share
    assert narrow > wide * 2
