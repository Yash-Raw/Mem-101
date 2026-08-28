"""Coarsen everything for free; only the health value is load-bearing."""
from __future__ import annotations

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.eval.exam import exam_answer
from memlab.pipeline import at
from memlab.privacy.classify import Kind, scan
from memlab.store.jsonl import JsonlStore
from memlab.types import Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Level = _solution.Level
apply = _solution.apply
redact = _solution.redact

PRIYA = Scope(user="priya")


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("rm") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    return s.all()


def _of(memories, needle):
    return next(m for m in memories if needle in m.content)


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.apply(memories, Level.COARSE, set(Kind))


def test_coarsening_is_per_kind(memories) -> None:
    address = _of(memories, "47 Halloway Road")
    phone = _of(memories, "07700 900412")
    health = _of(memories, "diagnosed with a gluten")
    assert redact(address, Level.COARSE).content == "Priya lives in Bristol"
    assert redact(phone, Level.COARSE).content == "Priya's phone number is on file"
    assert redact(health, Level.COARSE).content == (
        "Priya has a gluten intolerance last week"
    )


def test_third_party_has_no_coarse_form(memories) -> None:
    """Strip the employer and it is still a named person's occupation."""
    sam = _of(memories, "Sam is a nurse at St. Aubyn's")
    assert redact(sam, Level.COARSE).content == redact(sam, Level.TOKENISED).content
    assert "<third party>" in redact(sam, Level.COARSE).content


@pytest.mark.parametrize(
    "level,kinds,expected",
    [
        (Level.FULL, set(Kind), True),
        (Level.COARSE, set(Kind), True),
        (Level.COARSE, {Kind.HEALTH}, True),
        (Level.TOKENISED, set(Kind), False),
        (Level.TOKENISED, {Kind.ADDRESS, Kind.PHONE}, True),
        (Level.TOKENISED, {Kind.HEALTH}, False),
    ],
)
def test_what_each_policy_costs(memories, level, kinds, expected) -> None:
    out = apply(memories, level, kinds)
    assert exam_answer(out, PRIYA).is_correct is expected


def test_the_address_can_simply_be_destroyed(memories) -> None:
    """Tokenising contact details entirely, and the answer is unchanged."""
    out = apply(memories, Level.TOKENISED, {Kind.ADDRESS, Kind.PHONE})
    assert not any("47 Halloway Road" in m.content for m in out)
    assert not any("07700 900412" in m.content for m in out)
    assert exam_answer(out, PRIYA).is_correct


def test_only_the_health_value_is_load_bearing(memories) -> None:
    out = apply(memories, Level.TOKENISED, {Kind.HEALTH})
    assert not any("gluten" in m.content for m in out)
    assert not exam_answer(out, PRIYA).is_correct


def test_the_amount_removed_does_not_discriminate(memories) -> None:
    """5 tokens costs nothing; 7 costs the exam."""
    from memlab.assemble.simple import estimate_tokens

    phone = _of(memories, "07700 900412")
    health = _of(memories, "diagnosed with a gluten")
    dropped = {
        "phone": estimate_tokens(phone.content)
        - estimate_tokens(redact(phone, Level.TOKENISED).content),
        "health": estimate_tokens(health.content)
        - estimate_tokens(redact(health, Level.TOKENISED).content),
    }
    assert dropped == {"phone": 5, "health": 7}


def test_redaction_changes_the_id(memories) -> None:
    """Content-addressed, so a redacted record is a different record."""
    health = _of(memories, "diagnosed with a gluten")
    coarse = redact(health, Level.COARSE)
    assert coarse.id != health.id
    assert coarse.id != ""


def test_full_is_a_no_op(memories) -> None:
    """The null level, so the policy can be evaluated at all."""
    assert [m.id for m in apply(memories, Level.FULL, set(Kind))] == [
        m.id for m in memories
    ]


def test_unlabelled_memories_are_untouched(memories) -> None:
    labelled = {f.memory.id for f in scan(memories)}
    out = apply(memories, Level.TOKENISED, set(Kind))
    for before, after in zip(memories, out, strict=True):
        if before.id not in labelled:
            assert before.id == after.id
