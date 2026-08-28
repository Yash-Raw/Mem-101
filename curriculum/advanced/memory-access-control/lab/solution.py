"""Reference solution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
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
        if memory.scope.user != scope.user:
            return Decision(memory, Refused.WRONG_USER)

        # An agent may write in its own namespace or a shared one. Filing under
        # the bare user scope is claiming the user said it.
        speaker = memory.provenance.speaker
        if speaker not in self.first_party_speakers and memory.scope.agent is None:
            return Decision(memory, Refused.IMPERSONATION)

        when = memory.happened_at or memory.recorded_at
        if newest is not None and when > newest + self.skew:
            return Decision(memory, Refused.FUTURE_DATED)

        return Decision(memory)

    def admit(
        self, memories: list[Memory], scope: Scope, stored: list[Memory]
    ) -> tuple[list[Memory], list[Decision]]:
        """Split a batch into what is admitted and every refusal, with reasons.

        Refusals are returned rather than logged and dropped. A write path that
        silently discards is indistinguishable from one that never received
        anything, which is the failure `background-job-mechanics` spent a
        lesson on in a different stage.
        """
        newest = _newest(stored)
        decisions = [self.check(m, scope, newest) for m in memories]
        return [d.memory for d in decisions if d.admitted], [
            d for d in decisions if not d.admitted
        ]


def _newest(memories: list[Memory]) -> datetime | None:
    """The store's own clock -- the same reference `forget.decay` ages from."""
    stamps = [m.happened_at or m.recorded_at for m in memories]
    return max(stamps) if stamps else None
