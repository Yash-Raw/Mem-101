"""Say no to a write; assert the filter that says no to a read."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from memlab import labkit
from memlab.app.chat import ingest
from memlab.pipeline import at
from memlab.store import scopes
from memlab.store.jsonl import JsonlStore
from memlab.types import Memory, MemoryType, Provenance, Scope

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

Refused = _solution.Refused
WritePolicy = _solution.WritePolicy
_newest = _solution._newest

PRIYA = Scope(user="priya")
IN_RANGE = datetime(2026, 5, 16, tzinfo=UTC)
AHEAD = datetime(2027, 5, 16, tzinfo=UTC)


def _memory(content, speaker, agent, when, user="priya", authority=0.9):
    return Memory(
        content=content,
        type=MemoryType.SEMANTIC,
        scope=Scope(user=user, agent=agent),
        happened_at=when,
        provenance=Provenance(
            source_id=f"{speaker}:x", speaker=speaker, authority=authority
        ),
        confidence=authority,
    )


@pytest.fixture(scope="module")
def memories(tmp_path_factory):
    s = JsonlStore(tmp_path_factory.mktemp("ac") / "m.jsonl")
    ingest(s, PRIYA, at("A3"))
    return s.all()


def test_stub_is_runnable(memories) -> None:
    with pytest.raises(NotImplementedError):
        _lab.WritePolicy.default().check(memories[0], PRIYA, _newest(memories))


@pytest.mark.parametrize(
    "content,speaker,agent,when,user,expected",
    [
        ("a schedule fact", "calendar-agent", "calendar-agent", IN_RANGE, "priya", None),
        ("Priya likes cycling", "user", None, IN_RANGE, "priya", None),
        ("approved", "travel-agent", None, IN_RANGE, "priya", Refused.IMPERSONATION),
        ("leak", "travel-agent", None, IN_RANGE, "mallory", Refused.WRONG_USER),
        ("later", "travel-agent", "travel-agent", AHEAD, "priya", Refused.FUTURE_DATED),
    ],
)
def test_the_five_verdicts(
    memories, content, speaker, agent, when, user, expected
) -> None:
    decision = WritePolicy.default().check(
        _memory(content, speaker, agent, when, user), PRIYA, _newest(memories)
    )
    assert decision.refusal is expected
    assert decision.admitted is (expected is None)


def test_refusals_are_returned_not_dropped(memories) -> None:
    """A path that silently discards looks like one that received nothing."""
    batch = [
        _memory("a schedule fact", "calendar-agent", "calendar-agent", IN_RANGE),
        _memory("approved", "travel-agent", None, IN_RANGE),
        _memory("leak", "travel-agent", None, IN_RANGE, user="mallory"),
        _memory("later", "travel-agent", "travel-agent", AHEAD),
    ]
    admitted, refused = WritePolicy.default().admit(batch, PRIYA, memories)
    assert len(admitted) == 1
    assert [d.refusal for d in refused] == [
        Refused.IMPERSONATION, Refused.WRONG_USER, Refused.FUTURE_DATED
    ]


def test_impersonation_is_not_wrong_user(memories) -> None:
    """Same tenant, wrong attribution -- only one of the two is an incident."""
    policy, newest = WritePolicy.default(), _newest(memories)
    same_tenant = policy.check(
        _memory("approved", "travel-agent", None, IN_RANGE), PRIYA, newest
    )
    other_tenant = policy.check(
        _memory("leak", "travel-agent", None, IN_RANGE, user="mallory"), PRIYA, newest
    )
    assert same_tenant.refusal is Refused.IMPERSONATION
    assert other_tenant.refusal is Refused.WRONG_USER


def test_skew_is_a_day_not_zero(memories) -> None:
    """A write arriving now is newer than everything in a fixture."""
    policy, newest = WritePolicy.default(), _newest(memories)
    assert policy.skew == timedelta(days=1)
    just_now = _memory("fresh", "calendar-agent", "calendar-agent",
                       newest + timedelta(hours=12))
    assert policy.check(just_now, PRIYA, newest).admitted


def test_leak_check_is_an_invariant_not_a_detector(memories, tmp_path) -> None:
    """It can only fire if `Namespace.admits` is broken."""
    store = JsonlStore(tmp_path / "leak.jsonl")
    store.clear()
    store.add(list(memories))
    foreign = _memory("Mallory's salary is 90k", "user", None, IN_RANGE, user="mallory")
    store.add([foreign])

    assert any(m.id == foreign.id for m in store.all())
    assert not any(m.id == foreign.id for m in scopes.visible(store.all(), PRIYA))
    assert scopes.leak_check(store.all(), PRIYA) == []

    admits = scopes.Namespace.admits
    try:
        scopes.Namespace.admits = lambda self, m: True
        caught = scopes.leak_check(store.all(), PRIYA)
        assert len(caught) == 1
        assert caught[0].scope.user == "mallory"
    finally:
        scopes.Namespace.admits = admits


def test_the_rogue_is_never_even_examined(tmp_path) -> None:
    """Unnameable, so no candidate, no arbitration -- and the damage lands anyway."""
    from memlab.app import chat
    from memlab.evolve.conflict import slot_of

    original = chat._agent_memories
    try:
        chat._agent_memories = lambda s: [
            *original(s),
            _memory("Priya works at Meridian Health", "travel-agent", None,
                    AHEAD, authority=0.3),
        ]
        store = JsonlStore(tmp_path / "unnameable.jsonl")
        store.clear()
        ingest(store, PRIYA, at("A3").with_stage(admit=None))
    finally:
        chat._agent_memories = original

    rogue = next(m for m in store.all() if "Meridian" in m.content)
    assert slot_of(rogue) is None
    assert rogue.is_live, "nothing arbitrated it"
    assert rogue.confidence == 0.3


def test_the_shipped_store_holds_the_invariant(memories) -> None:
    """The assertion this module puts in CI."""
    assert scopes.leak_check(memories, PRIYA) == []
