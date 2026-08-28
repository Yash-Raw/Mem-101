"""Three correct derived beliefs, and every way of storing them is worse."""
from __future__ import annotations

from dataclasses import replace as dc_replace
from datetime import UTC, datetime

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.eval.exam import exam_from_context
from memlab.evolve.promote import analyse
from memlab.pipeline import at
from memlab.retrieve.scoped import eligible
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope, Tier

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Refusal = _solution.Refusal
compose = _solution.compose
groups = _solution.groups
reflect = _solution.reflect

PRIYA = Scope(user="priya")
NOW = datetime(2026, 8, 27, tzinfo=UTC)


def _fresh(tmp_path, tag):
    pipeline = at("A2")
    store = JsonlStore(tmp_path / f"{tag}.jsonl")
    store.clear()
    ingest(store, PRIYA, pipeline)
    return store, pipeline


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    return _fresh(tmp_path_factory.mktemp("reflect"), "base")


def _lowest_passing(memories, pipeline):
    for budget in range(40, 90):
        if exam_from_context(
            memories, PRIYA, k=5, pipeline=pipeline, budget=budget
        ).is_correct:
            return budget
    return None


def test_stub_is_runnable(base) -> None:
    store, _ = base
    with pytest.raises(NotImplementedError):
        _lab.groups(store.all(), PRIYA)


def test_similarity_ranks_a_contradiction_first(base) -> None:
    """I3's null result, applied to reflection and failing harder."""
    store, _ = base
    report = analyse(store.all(), PRIYA)
    assert len(report.candidates) == 20
    assert report.promoted == []
    top = report.candidates[0]
    assert "drinks tea" in top.a.content
    assert "three coffees" in top.b.content


def test_most_similarity_candidates_pair_unrelated_slots(base) -> None:
    """14 of 20. The first genuine dietary relation sits sixth."""
    from memlab.evolve.conflict import slot_of

    store, _ = base
    candidates = analyse(store.all(), PRIYA).candidates
    unrelated = sum(
        1 for c in candidates if not (slot_of(c.a) and slot_of(c.a) == slot_of(c.b))
    )
    assert unrelated == 14


def test_structure_finds_four_groups(base) -> None:
    store, _ = base
    usable = [g for g in groups(store.all(), PRIYA) if len(g.members) >= 2]
    assert {g.slot for g in usable} == {
        "diet", "beverage", "employer", "occupation_other"
    }


def test_the_third_party_group_is_refused(base) -> None:
    """Composing it writes that Priya works night shifts as a charge nurse."""
    store, _ = base
    group = next(g for g in groups(store.all(), PRIYA) if g.slot == "occupation_other")
    assert group.refusal is Refusal.THIRD_PARTY
    assert all(m.entities == ("samira",) for m in group.members)


def test_a_retired_member_is_not_a_reason_to_refuse(base) -> None:
    """It is simply not a member; the slot's history is untouched."""
    store, _ = base
    diet = next(g for g in groups(store.all(), PRIYA) if g.slot == "diet")
    assert diet.ok
    assert len(diet.members) == 4
    assert any(
        not m.is_live for m in store.all() if "vegetarian" in m.content
    ), "and the retired belief is still in the store"


def test_three_are_derived_and_all_are_traceable(base) -> None:
    store, _ = base
    insights = reflect(store.all(), PRIYA)
    assert len(insights) == 3
    ids = {m.id for m in store.all()}
    for m in insights:
        assert m.derived_from, "every insight names its sources"
        assert set(m.derived_from) <= ids, "and every source is in the store"


def test_derived_beliefs_are_invisible_until_scored(tmp_path_factory) -> None:
    """0 of 3 eligible: created after the pass that assigns tiers."""
    store, _pipeline = _fresh(tmp_path_factory.mktemp("invisible"), "inv")
    insights = reflect(store.all(), PRIYA)
    assert all(m.tier is Tier.WORKING for m in insights)
    store.add(insights)
    pool = eligible(store.all(), PRIYA)
    assert len(pool) == 18
    assert sum(1 for m in pool if m.id in {x.id for x in insights}) == 0


def test_scored_they_rank_first_and_second(tmp_path_factory) -> None:
    from memlab.app.chat import ask
    from memlab.eval.exam import QUESTION

    store, pipeline = _fresh(tmp_path_factory.mktemp("scored"), "sc")
    insights = reflect(store.all(), PRIYA)
    store.add(insights)
    store.replace(pipeline.decay(store.all()))
    pipeline.vectors.index(store.all())
    hits = ask(store, PRIYA, QUESTION, k=5, pipeline=pipeline)[1]
    derived = {m.id for m in insights}
    assert [h.memory.id in derived for h in hits][:2] == [True, True]
    assert sum(h.memory.id in derived for h in hits) == 2

    scored = {m.id: m for m in store.all()}
    diet = next(m for m in insights if m.content.startswith("diet:"))
    assert scored[diet.id].salience == 0.899, "the highest in the store"
    assert scored[diet.id].salience == max(m.salience for m in store.all())


def test_both_policies_make_the_budget_worse(tmp_path_factory) -> None:
    """51 -> 55 joined, 51 -> 56 replacing. Correct, and not an improvement."""
    root = tmp_path_factory.mktemp("budget")

    store, pipeline = _fresh(root, "none")
    assert _lowest_passing(store.all(), pipeline) == 51

    store, pipeline = _fresh(root, "join")
    store.add(reflect(store.all(), PRIYA))
    store.replace(pipeline.decay(store.all()))
    assert _lowest_passing(store.all(), pipeline) == 55

    store, pipeline = _fresh(root, "swap")
    insights = reflect(store.all(), PRIYA)
    sources = {i for m in insights for i in m.derived_from}
    store.replace([
        dc_replace(
            m, invalid_at=NOW,
            superseded_by=next(x.id for x in insights if m.id in x.derived_from),
        )
        if m.id in sources else m
        for m in store.all()
    ] + insights)
    store.replace(pipeline.decay(store.all()))
    assert _lowest_passing(store.all(), pipeline) == 56


def test_slot_values_52_and_this_lessons_51_agree(tmp_path_factory) -> None:
    """slot-value swept discrete budgets and never tried 51. Both pass."""
    store, pipeline = _fresh(tmp_path_factory.mktemp("boundary"), "b")
    for budget in (52, 51):
        assert exam_from_context(
            store.all(), PRIYA, k=5, pipeline=pipeline, budget=budget
        ).is_correct
    assert not exam_from_context(
        store.all(), PRIYA, k=5, pipeline=pipeline, budget=50
    ).is_correct


def test_reflection_is_not_wired_into_any_pipeline() -> None:
    """Like promote() before it: the deferral stays visible in code."""
    for module in ("I8", "A1", "A2"):
        pipeline = at(module)
        assert reflect not in (pipeline.consolidate, pipeline.decay, pipeline.anchor)


def test_compose_is_a_template_not_a_generation(base) -> None:
    store, _ = base
    diet = next(g for g in groups(store.all(), PRIYA) if g.slot == "diet")
    composed = compose(diet, PRIYA)
    for member in diet.members:
        assert member.content in composed.content, "checkable against every source"
    assert composed.confidence == min(m.confidence for m in diet.members)
