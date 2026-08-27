"""Similarity cannot identify corroboration. Asserted."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

analyse = _solution.analyse
best_threshold_accuracy = _solution.best_threshold_accuracy
corroborate = _solution.corroborate
labelled_scores = _solution.labelled_scores
subject_of = _solution.subject_of

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    store = JsonlStore(tmp_path_factory.mktemp("promo") / "m.jsonl")
    ingest(store, PRIYA, at("I3"))
    return store.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.subject_of(memories[0], PRIYA)


def test_beliefs_about_the_user_have_a_subject(memories) -> None:
    """Without the fallback, every fact about Priya is invisible here."""
    vegetarian = next(m for m in memories if m.content == "Priya is vegetarian")
    assert vegetarian.entities == ()
    assert subject_of(vegetarian, PRIYA) == frozenset({"priya"})


def test_candidates_are_found_and_none_promoted(memories) -> None:
    report = analyse(memories, PRIYA)
    assert len(report.candidates) > 40
    assert report.promoted == []
    assert "defer to conflict detection" in report.verdict


def test_corroboration_ranks_below_a_refinement() -> None:
    """The finding the lesson is built on."""
    scored = {label: s for s, _, _, label in labelled_scores()}
    assert scored["refinement"] > scored["corroboration"]
    assert scored["corroboration"] > scored["contradiction"]


def test_no_threshold_separates_corroboration() -> None:
    """Best possible single cutoff still gets a labelled pair wrong."""
    assert best_threshold_accuracy() < 1.0


def test_corroborate_records_what_justified_the_boost(memories) -> None:
    """Written, and deliberately not called until I4."""
    target = next(m for m in memories if m.content == "Priya is vegetarian")
    supporter = next(m for m in memories if m.content == "Priya does not eat meat")
    boosted = corroborate(target, [supporter])

    assert boosted.confidence > target.confidence
    assert supporter.provenance.source_id in boosted.derived_from
    assert boosted.id == target.id, "corroboration must not change identity"


def test_extracted_claims_leave_headroom(memories) -> None:
    """A single unconfirmed source is not certainty.

    Beginner stored everything at 1.0, which quietly made corroboration
    impossible -- there was nowhere for confidence to go.
    """
    from memlab.extract.pipeline import SINGLE_SOURCE_CONFIDENCE

    assert SINGLE_SOURCE_CONFIDENCE < 1.0
    extracted = [m for m in memories if m.provenance.speaker == "user"]
    # 0.9 for a single source; 1.0 only where deduplication corroborated it.
    assert {m.confidence for m in extracted} == {SINGLE_SOURCE_CONFIDENCE, 1.0}
    corroborated = [m for m in extracted if m.confidence > SINGLE_SOURCE_CONFIDENCE]
    assert [m.content for m in corroborated] == ["Priya works at Calico Systems"]


def test_relayed_claims_are_believed_as_much_as_their_source(memories) -> None:
    """The Berlin hearsay must not sit at the same confidence as Priya's own words."""
    berlin = next(m for m in memories if "Berlin" in m.content)
    assert berlin.confidence == berlin.provenance.authority == 0.3

    first_party = next(m for m in memories if m.content == "Priya is vegetarian")
    assert berlin.confidence < first_party.confidence


def test_the_pipeline_does_not_call_promote(memories) -> None:
    """The deferral is real, not just documented.

    Deduplication may raise confidence on a merged survivor -- that is a
    different mechanism, and it acts on certainty rather than on similarity.
    Nothing here has a `derived_from` from promotion.
    """
    assert all(not m.derived_from for m in memories)
