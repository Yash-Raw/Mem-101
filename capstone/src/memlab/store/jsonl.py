"""An append-only JSONL store.

Append-only is the right first store: it is trivially durable, trivially
inspectable, and it makes provenance free. It also cannot express an update,
which is precisely the wall Level 2 runs into.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..types import Memory, MemoryType, Provenance, Scope, Tier


def _parse_dt(v: str | None) -> datetime | None:
    return datetime.fromisoformat(v) if v else None


class JsonlStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, memories: list[Memory]) -> int:
        """Append. Content-addressed ids make re-ingesting a turn idempotent."""
        existing = {m.id for m in self.all()}
        fresh = [m for m in memories if m.id not in existing]
        with self.path.open("a") as fh:
            for m in fresh:
                fh.write(m.to_json() + "\n")
        return len(fresh)

    def all(self) -> list[Memory]:
        if not self.path.exists():
            return []
        return [self._revive(json.loads(line)) for line in self.path.read_text().splitlines() if line.strip()]

    def live(self) -> list[Memory]:
        return [m for m in self.all() if m.is_live]

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)

    def replace(self, memories: list[Memory]) -> int:
        """Rewrite the log wholesale.

        Only consolidation needs this -- merging duplicates and retiring
        superseded beliefs produces a new set, not an append. It is the one
        operation that breaks append-only, which is why it lives behind an
        explicit method rather than being reachable from `add`.
        """
        self.clear()
        with self.path.open("a") as fh:
            for m in memories:
                fh.write(m.to_json() + "\n")
        return len(memories)

    @staticmethod
    def _revive(d: dict) -> Memory:
        return Memory(
            content=d["content"],
            type=MemoryType(d["type"]),
            scope=Scope(**d["scope"]),
            provenance=Provenance(**d["provenance"]),
            happened_at=_parse_dt(d["happened_at"]),
            recorded_at=_parse_dt(d["recorded_at"]),
            invalid_at=_parse_dt(d["invalid_at"]),
            superseded_by=d.get("superseded_by"),
            confidence=d["confidence"],
            salience=d["salience"],
            tier=Tier(d["tier"]),
            access_count=d["access_count"],
            entities=tuple(d.get("entities", ())),
            id=d["id"],
        )
