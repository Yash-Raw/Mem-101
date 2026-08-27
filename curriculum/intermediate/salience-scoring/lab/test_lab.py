"""Salience is importance; ranking wants relevance. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.eval.exam import QUESTION
from memlab.fixtures import load_turns
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import MemoryType, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

apply = _solution.apply
rank_with_salience = _solution.rank_with_salience
record_use = _solution.record_use
score = _solution.score

PRIYA = Scope(user="priya")
EMPLOYER = "Priya works at Calico Systems"


TURNS = {f"s{t['session']}:{t['ts']}": t["text"] for t in load_turns(user_only=True)}


@pytest.fixture(scope="module")
def scored(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("sal") / "m.jsonl")
    ingest(store, PRIYA, at("I4"))
    return apply(store.all(), TURNS)


def employer_rank(memories, weight: float) -> int:
    ranked = rank_with_salience(QUESTION, memories, weight)
    return next(i for i, (_, m) in enumerate(ranked, 1) if m.content == EMPLOYER)


def test_stub_is_runnable(scored) -> None:
    with pytest.raises(NotImplementedError):
        _lab.score(scored[0])


def test_salience_discriminates(scored) -> None:
    """Beginner left every memory at 0.5, so nothing could be ranked down."""
    live = {m.salience for m in scored if m.is_live}
    assert len(live) == 6
    assert min(live) == 0.5 and max(live) == 0.95


def test_the_procedure_scores_highest(scored) -> None:
    """Correctly: Priya taught it deliberately and said the order mattered."""
    top = max((m for m in scored if m.is_live), key=lambda m: m.salience)
    assert top.type is MemoryType.PROCEDURAL
    assert top.salience == 0.95


def test_adding_salience_to_the_ranker_makes_it_worse(scored) -> None:
    """The lesson's central measurement."""
    assert employer_rank(scored, 0.0) == 20
    assert employer_rank(scored, 0.2) == 21
    assert employer_rank(scored, 0.5) == 22


def test_and_promotes_the_procedure_to_first(scored) -> None:
    top = rank_with_salience(QUESTION, scored, 0.5)[0][1]
    assert top.type is MemoryType.PROCEDURAL


def test_reinforcement_helps_and_cannot_rescue_it(scored) -> None:
    """Use is strong evidence and a weak prior -- 0.05 against a 0.45 head start."""
    needed = {m.id for m in scored if "Calico" in m.content or "gluten" in m.content}
    used = apply(record_use(scored, needed), TURNS)
    boosted = [m for m in used if m.id in needed]
    assert all(m.access_count == 1 for m in boosted)
    assert all(m.salience > 0.5 for m in boosted), "use raises them"
    assert rank_with_salience(QUESTION, used, 0.5)[0][1].type is MemoryType.PROCEDURAL


def test_rescoring_without_the_turns_silently_loses_the_explicit_signal(scored) -> None:
    """A real fragility: `apply` reads explicit markers from the ORIGINATING turn.

    Re-score without passing them and the strongest signal in the table
    disappears -- no error, just a quietly worse store. Every caller must carry
    the turn text.
    """
    procedure = max(scored, key=lambda m: m.salience)
    blind = next(m for m in apply(scored, {}) if m.id == procedure.id)
    assert blind.salience < procedure.salience


def test_hearsay_scores_below_first_party(scored) -> None:
    berlin = next(m for m in scored if "Berlin" in m.content)
    first_party = next(m for m in scored if m.content == "Priya does not eat meat")
    assert berlin.salience < first_party.salience
