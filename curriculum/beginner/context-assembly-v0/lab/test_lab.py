"""Framing and the budget line. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.assemble.simple import estimate_tokens
from memlab.retrieve.embedding import EmbeddingRetriever
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

assemble = _solution.assemble
assemble_truncating = _solution.assemble_truncating

PRIYA = Scope(user="priya")
Q = "where do I work and what should I not eat?"


@pytest.fixture(scope="module")
def hits(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("asm") / "m.jsonl")
    ingest(store, PRIYA)
    return EmbeddingRetriever().search(Q, store.all(), PRIYA, k=8)


def test_stub_is_runnable(hits) -> None:
    with pytest.raises(NotImplementedError):
        _lab.assemble(hits, 200)


def test_memories_are_framed_as_beliefs_not_facts(hits) -> None:
    """The cheapest reliability improvement in the system."""
    text = assemble(hits, 200)
    assert "recalled beliefs" in text
    assert "may be out of date" in text


def test_every_memory_is_dated(hits) -> None:
    for line in [x for x in assemble(hits, 200).splitlines() if x.startswith("- ")]:
        assert line[2] == "[" and line[13] == "]", f"undated: {line}"


def test_the_budget_is_respected_including_the_header(hits) -> None:
    for budget in (40, 60, 120, 200):
        assert estimate_tokens(assemble(hits, budget)) <= budget


def test_a_smaller_budget_drops_whole_memories(hits) -> None:
    big, small = assemble(hits, 200), assemble(hits, 60)
    assert small.count("\n- ") < big.count("\n- ")
    for line in [x for x in small.splitlines() if x.startswith("- ")]:
        assert line in big, "a kept memory must be byte-identical, never shortened"


def test_the_truncating_variant_emits_a_fragment(hits) -> None:
    """The contrast that makes the rule concrete.

    At 60 tokens the truncating version emits
    `- [2025-09-14] Priya's weekly report process`
    which READS as a complete statement and has lost the entire workflow.
    That is the hazard: not obviously broken, just silently wrong.
    """
    correct = {x for x in assemble(hits, 60).splitlines() if x.startswith("- ")}
    truncated = {x for x in assemble_truncating(hits, 60).splitlines() if x.startswith("- ")}
    fragments = truncated - correct
    assert fragments, "the truncating version cuts a memory mid-sentence"

    full = {h.memory.content for h in hits}
    for f in fragments:
        body = f.split("] ", 1)[1]
        source = next((c for c in full if c.startswith(body)), None)
        assert source is not None, f"{body!r} should be a prefix of a real memory"
        assert len(body) < len(source), "and a strictly shorter one"


def test_ordering_is_by_score_not_date(hits) -> None:
    lines = [x for x in assemble(hits, 400).splitlines() if x.startswith("- ")]
    dates = [x[3:13] for x in lines]
    assert dates != sorted(dates), "score order, so the best memory leads"
