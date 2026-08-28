"""Lab: say no to a write, and assert the filter that says no to a read.

    uv run python curriculum/advanced/memory-access-control/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum

from memlab.types import Memory, Scope


class Refused(Enum):
    """Why a write was not admitted."""

    WRONG_USER = "wrong user"          # crossing a tenant boundary
    IMPERSONATION = "impersonation"    # an agent writing as the user
    FUTURE_DATED = "future dated"      # a clock that would re-age the store


@dataclass(frozen=True)
class Decision:
    memory: Memory
    refusal: Refused | None = None

    @property
    def admitted(self) -> bool:
        return self.refusal is None


@dataclass(frozen=True)
class WritePolicy:
    """The three checks, in the order that makes each one cheap.

    `skew` is how far ahead of the store's newest event a write may be dated.
    Not zero: a write genuinely arriving now is newer than everything in a
    fixture, and a policy that rejects the present is a policy nobody runs.
    """

    skew: timedelta = timedelta(days=1)
    first_party_speakers: frozenset[str] = frozenset({"user"})

    @classmethod
    def default(cls) -> WritePolicy:
        return cls()

    def check(self, memory: Memory, scope: Scope, newest: datetime | None) -> Decision:
        raise NotImplementedError("implement check")

    def admit(
        self, memories: list[Memory], scope: Scope, stored: list[Memory]
    ) -> tuple[list[Memory], list[Decision]]:
        """Split a batch into what is admitted and every refusal, with reasons.

        Refusals are returned rather than logged and dropped. A write path that
        silently discards is indistinguishable from one that never received
        anything, which is the failure `background-job-mechanics` spent a
        lesson on in a different stage.
        """
        raise NotImplementedError("implement admit")


def _newest(memories: list[Memory]) -> datetime | None:
    """The store's own clock -- the same reference `forget.decay` ages from."""
    stamps = [m.happened_at or m.recorded_at for m in memories]
    return max(stamps) if stamps else None


IN_RANGE = datetime(2026, 5, 16, tzinfo=UTC)
AHEAD = datetime(2027, 5, 16, tzinfo=UTC)


def _memory(content, speaker, agent, when, user="priya", authority=0.9):
    from memlab.types import MemoryType, Provenance

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


def main() -> None:
    from memlab.app import chat
    from memlab.app.chat import ask, ingest
    from memlab.pipeline import at
    from memlab.retrieve.scoped import eligible
    from memlab.store import scopes
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-authorise.jsonl")
    store.clear()
    ingest(store, scope, at("A3"))
    memories = store.all()
    policy = WritePolicy.default()
    newest = _newest(memories)

    print(f"store clock (newest event): {newest.date()}   "
          f"skew allowed: {policy.skew}\n")
    cases = [
        ("the corpus agent writes, in its own namespace",
         _memory("a schedule fact", "calendar-agent", "calendar-agent", IN_RANGE)),
        ("an agent files under the bare user scope",
         _memory("Priya approved the relocation", "travel-agent", None, IN_RANGE)),
        ("an agent writes into another tenant",
         _memory("leak", "travel-agent", None, IN_RANGE, user="mallory")),
        ("an agent writes dated a year ahead",
         _memory("Priya will move", "travel-agent", "travel-agent", AHEAD)),
        ("the user says something",
         _memory("Priya likes cycling", "user", None, IN_RANGE)),
    ]
    for label, memory in cases:
        decision = policy.check(memory, scope, newest)
        verdict = "ADMIT" if decision.admitted else f"refuse: {decision.refusal.value}"
        print(f"   {label:46} {verdict}")

    batch = [m for _label, m in cases[:4]]
    admitted, refused = policy.admit(batch, scope, memories)
    print(f"\n   admitted {len(admitted)} of {len(batch)}; "
          "refusals returned, not dropped:")
    for decision in refused:
        print(f"      {decision.refusal.value:16} {decision.memory.content[:40]}")

    print(f"\n   {'':34}{'store':>7}{'eligible':>10}")
    original = chat._agent_memories
    for label, when in (("no rogue", None), ("rogue dated inside the corpus", IN_RANGE),
                        ("rogue dated a year ahead", AHEAD)):
        if when is None:
            chat._agent_memories = original
        else:
            def patched(s, when=when):
                # The impersonating shape: filed under the bare user scope,
                # which is what the unguarded pipeline accepts.
                # The travel agent's real trust level, so the rogue is not
                # itself retrievable and the table shows only the damage its
                # timestamp does to everything else.
                return [*original(s), _memory(
                    "Priya works at Meridian Health", "travel-agent", None, when,
                    authority=0.3,
                )]
            chat._agent_memories = patched
        pipeline = at("A3").with_stage(admit=None)   # unguarded, to show the damage
        probe = JsonlStore(f"/tmp/memlab-auth-{label[:6]}.jsonl")
        probe.clear()
        ingest(probe, scope, pipeline)
        if pipeline.vectors is not None:
            pipeline.vectors.index(probe.all())
        top = [h.memory.content[:26] for h in
               ask(probe, scope, "where do I work?", k=2, pipeline=pipeline)[1]]
        print(f"   {label:34}{len(probe.all()):>7}{len(eligible(probe.all(), scope)):>10}"
              f"   {top}")
    chat._agent_memories = original

    foreign = _memory("Mallory's salary is 90k", "user", None, IN_RANGE, user="mallory")
    store.add([foreign])
    print(f"\n   leak_check with the filter intact  "
          f"{len(scopes.leak_check(store.all(), scope)):>4}")
    admits = scopes.Namespace.admits
    scopes.Namespace.admits = lambda self, m: True
    caught = scopes.leak_check(store.all(), scope)
    print(f"   leak_check with admits() broken    {len(caught):>4}")
    for m in caught:
        print(f"      {m.scope.user}: {m.content}")
    scopes.Namespace.admits = admits


if __name__ == "__main__":
    main()
