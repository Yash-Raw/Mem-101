"""The memory record.

The fields chosen here are what Intermediate and Advanced depend on. Notably:
two clocks (`happened_at` vs `recorded_at`), because one timestamp is a bug you
cannot fix later; and `provenance`, because a memory written without it can
never be deleted on request -- nothing identifies what to delete.
"""
from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime


class MemoryType(str, enum.Enum):
    """Types differ by lifecycle and update rule, not by vibe."""

    EPISODIC = "episodic"      # a thing that happened, at a time
    SEMANTIC = "semantic"      # a durable fact or preference
    PROCEDURAL = "procedural"  # how to do something
    WORKING = "working"        # scratch, dies with the task


class Tier(str, enum.Enum):
    SCRATCH = "scratch"
    WORKING = "working"
    LONG_TERM = "long_term"


@dataclass(frozen=True, slots=True)
class Scope:
    """The key every read must filter on before it ranks anything."""

    user: str
    agent: str | None = None
    session: str | None = None

    def matches(self, other: Scope) -> bool:
        if self.user != other.user:
            return False
        return not (self.agent and other.agent and self.agent != other.agent)


@dataclass(frozen=True, slots=True)
class Provenance:
    """Who said it, where, and whether we consider the source authoritative.

    Keeping `speaker` distinct from `authority` is what stops 'the user
    mentioned their friend believes X' from being stored as 'X'.
    """

    source_id: str            # the episode/turn this came from
    speaker: str              # "user" | "assistant" | agent name
    authority: float = 1.0    # 1.0 = first-party assertion; lower = hearsay


@dataclass(frozen=True, slots=True)
class Memory:
    content: str
    type: MemoryType
    scope: Scope
    provenance: Provenance
    happened_at: datetime | None = None   # event time -- when it was true
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    valid_from: datetime | None = None    # A1: when the fact became true in the world
    valid_to: datetime | None = None      # A1: when it stopped being true -- NOT invalid_at
    invalid_at: datetime | None = None    # set on supersession; never delete
    superseded_by: str | None = None
    confidence: float = 1.0
    salience: float = 0.5
    tier: Tier = Tier.WORKING
    access_count: int = 0
    entities: tuple[str, ...] = ()
    # Source ids of the memories this one was derived from. Empty for anything
    # extracted directly from a turn; populated for summaries and promotions.
    # Added in Level 2, when summarisation first needed it -- see
    # `summarization-and-compaction` for why adding it late is cheap now and
    # would not have been after a million summaries existed.
    derived_from: tuple[str, ...] = ()
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", self._derive_id())

    def _derive_id(self) -> str:
        """Content-addressed, so re-ingesting the same turn is idempotent."""
        key = f"{self.scope.user}|{self.type.value}|{self.content}|{self.provenance.source_id}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    @property
    def is_live(self) -> bool:
        return self.invalid_at is None

    def supersede(
        self,
        by: str,
        at: datetime,
        found_out: datetime | None = None,
        event_end: bool = False,
    ) -> Memory:
        """Retire a belief without destroying the audit trail.

        `at` is when the fact stopped being true; `found_out` is when the store
        learned that. They are different instants and the gap between them is
        the interesting part -- a store that cannot report it cannot answer
        "how long were you wrong?".

        `found_out` defaults to `at`, and `event_end` is off, which together
        are what every caller meant before the two axes were separated -- one
        instant, written to one field.
        """
        return replace(
            self,
            valid_to=at if event_end else self.valid_to,
            invalid_at=found_out if found_out is not None else at,
            superseded_by=by,
        )

    def to_json(self) -> str:
        d = asdict(self)
        d["type"] = self.type.value
        d["tier"] = self.tier.value
        for k in ("happened_at", "recorded_at", "invalid_at", "valid_from", "valid_to"):
            d[k] = d[k].isoformat() if d[k] else None
        return json.dumps(d, sort_keys=True)
