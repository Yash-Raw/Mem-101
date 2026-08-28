"""Every early number this metric produced was the metric."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.fixtures import load_gold
from memlab.pipeline import at
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

anchoring = _solution.anchoring
arbitration = _solution.arbitration
extraction = _solution.extraction
report = _solution.report
resolution = _solution.resolution

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("cp") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    return s.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.extraction(memories)


def test_all_four_scorable_stages_pass(memories) -> None:
    scored = {m.stage: m for m in report(memories, PRIYA) if m.scorable}
    assert set(scored) == {"extract", "resolve", "arbitrate", "anchor"}
    assert all(m.rate == 1.0 for m in scored.values())


def test_located_is_reported_separately_from_entries(memories) -> None:
    """4-of-4 and 4-of-6 are different situations at the same rate."""
    scored = {m.stage: m for m in report(memories, PRIYA) if m.scorable}
    assert (scored["arbitrate"].total, scored["arbitrate"].unmatched) == (5, 1)
    assert (scored["anchor"].total, scored["anchor"].unmatched) == (6, 2)
    assert (scored["extract"].total, scored["extract"].unmatched) == (4, 0)


def test_folding_unmatched_in_looks_like_a_regression(memories) -> None:
    """The stretch: wrong, stable, and internally consistent."""
    scored = {m.stage: m for m in report(memories, PRIYA) if m.scorable}
    assert round(scored["arbitrate"].scored / scored["arbitrate"].total, 3) == 0.800
    assert round(scored["anchor"].scored / scored["anchor"].total, 3) == 0.667


def test_the_four_buggy_versions_reproduce_their_numbers(memories) -> None:
    """The lesson's table, executable. Each is a plausible first attempt."""
    from memlab.evolve.conflict import slot_of
    from memlab.temporal.clocks import event_start
    from memlab.types import MemoryType

    gold = load_gold()

    # 1. substring-match gold's paraphrased supersession values -> 0.733
    wanted = [s["value"] for s in gold["pii"]] + [
        s[k]["value"]
        for s in gold["supersessions"]
        for k in ("original", "replacement", "addition")
        if k in s
    ]
    found = sum(
        1
        for w in wanted
        if any(w.split(",")[0].lower() in m.content.lower() for m in memories)
    )
    assert round(found / len(wanted), 3) == 0.733

    # 2. match the phrase, ignore the session -> 0.500
    entries = [e for e in gold["relative_time"] if e["resolves_to"]]
    right = 0
    for entry in entries:
        first = next(
            (m for m in memories if entry["phrase"].lower() in m.content.lower()), None
        )
        got = event_start(first).date() if first and event_start(first) else None
        right += got == entry["resolves_to"]
    assert round(right / len(entries), 3) == 0.5

    # 3 and 4. match supersession values as text, and require every claim
    #          in the slot retired -> 0.600 both ways
    supers = [s for s in gold["supersessions"] if "replacement" in s]
    by_text = 0
    for entry in supers:
        live = " ".join(
            m.content
            for m in memories
            if m.is_live and m.type is MemoryType.SEMANTIC
        )
        want, stale = entry["replacement"]["value"], entry["original"]["value"]
        by_text += want.split()[0] in live and stale.split()[0] not in live
    assert round(by_text / len(supers), 3) == 0.6

    by_all_retired = 0
    for entry in supers:
        session = f"s{entry['original']['session']}:"
        claims = [
            m
            for m in memories
            if m.type is MemoryType.SEMANTIC
            and m.provenance.source_id.startswith(session)
            and slot_of(m) == entry["subject"]
        ]
        by_all_retired += bool(claims) and all(not m.is_live for m in claims)
    assert round(by_all_retired / len(supers), 3) == 0.6


def test_the_unlocated_anchor_entries_are_unlocatable(memories) -> None:
    """A question produces no memory; a phrase-less entry has no phrase."""
    gold = load_gold()["relative_time"]
    spark = next(e for e in gold if e["phrase"] == "last month" and e["session"] == 3)
    assert spark["resolves_to"]
    assert not any(
        "spark job last month" in m.content.lower() for m in memories
    ), "the session-3 phrase is inside a question"

    inferred = next(e for e in gold if e["phrase"] == "Very proud of her")
    assert "no explicit time phrase" in inferred["note"]


def test_the_unlocated_arbitration_entry_is_a_modelling_difference(memories) -> None:
    """commute names the replacement's session; the change is past-tense."""
    from memlab.evolve.conflict import slot_of

    commute = next(
        e for e in load_gold()["supersessions"] if e["subject"] == "commute"
    )
    session = f"s{commute['original']['session']}:"
    claims = [
        m
        for m in memories
        if m.provenance.source_id.startswith(session) and slot_of(m) == "commute"
    ]
    assert claims and all(m.is_live for m in claims)


def test_beverage_has_a_correctly_live_sibling(memories) -> None:
    """Requiring every claim retired scores "still drinks tea" as a failure."""
    from memlab.evolve.conflict import slot_of
    from memlab.types import MemoryType

    claims = [
        m
        for m in memories
        if m.provenance.source_id.startswith("s4:")
        and slot_of(m) == "beverage"
        and m.type is MemoryType.SEMANTIC
    ]
    assert len(claims) == 2
    assert sum(1 for m in claims if m.is_live) == 1
    assert arbitration(memories, PRIYA).rate == 1.0


def test_three_stages_have_no_metric_and_say_why(memories) -> None:
    unscorable = [m for m in report(memories, PRIYA) if not m.scorable]
    assert {m.stage for m in unscorable} == {"dedupe", "decay", "rank"}
    assert all(m.note and m.rate is None for m in unscorable)


def test_extraction_is_recall_only(memories) -> None:
    """Precision needs an enumeration of what should not be extracted."""
    metric = extraction(memories)
    assert metric.total == len(load_gold()["pii"])
    assert metric.scored == metric.total


def test_resolution_reaches_one_canonical_id(memories) -> None:
    assert resolution(memories).rate == 1.0
