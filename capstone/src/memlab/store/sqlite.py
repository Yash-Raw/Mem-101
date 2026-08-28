"""The store nobody reaches for, and usually should.

`scope-then-rank` applies three filters in Python -- scope, validity, tier --
by loading every memory and discarding most of them. On 37 records that is
invisible. It is also a full scan, and the filters are exactly the shape a
relational store answers with an index.

SQLite is in the standard library, gives ACID writes, indexed predicates, and
full-text search over content, and needs no server. The reason to know this is
that "memory layer" is often taken to mean "vector database", and most of what
a memory store actually does -- filter by owner, by validity, by tier, by type,
ordered by time -- is a WHERE clause.

The vector work is real and it is one column of the problem.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from ..types import Memory, MemoryType, Provenance, Scope, Tier

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id           TEXT PRIMARY KEY,
    content      TEXT NOT NULL,
    type         TEXT NOT NULL,
    user         TEXT NOT NULL,
    agent        TEXT,
    session      TEXT,
    speaker      TEXT NOT NULL,
    source_id    TEXT NOT NULL,
    authority    REAL NOT NULL,
    happened_at  TEXT,
    valid_from   TEXT,
    valid_to     TEXT,
    recorded_at  TEXT NOT NULL,
    invalid_at   TEXT,
    superseded_by TEXT,
    confidence   REAL NOT NULL,
    salience     REAL NOT NULL,
    tier         TEXT NOT NULL,
    access_count INTEGER NOT NULL,
    entities     TEXT NOT NULL,
    derived_from TEXT NOT NULL
);
-- The three filters scope-then-rank applies in Python, as indexes.
CREATE INDEX IF NOT EXISTS idx_scope    ON memories(user, agent);
CREATE INDEX IF NOT EXISTS idx_validity ON memories(invalid_at);
CREATE INDEX IF NOT EXISTS idx_tier     ON memories(tier);
CREATE INDEX IF NOT EXISTS idx_source   ON memories(source_id);
"""


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class SqliteStore:
    """Implements the same interface as JsonlStore: add, all, live, replace, clear."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.scanned = 0   # rows the engine returned, for the lesson's measurement

    # --- writes ----------------------------------------------------------
    def add(self, memories: list[Memory]) -> int:
        rows = [self._row(m) for m in memories]
        before = self._count()
        self.db.executemany(
            "INSERT OR IGNORE INTO memories VALUES "
            "(:id,:content,:type,:user,:agent,:session,:speaker,:source_id,:authority,"
            ":happened_at,:valid_from,:valid_to,:recorded_at,:invalid_at,:superseded_by,:confidence,:salience,"
            ":tier,:access_count,:entities,:derived_from)",
            rows,
        )
        self.db.commit()
        return self._count() - before

    def replace(self, memories: list[Memory]) -> int:
        self.db.execute("DELETE FROM memories")
        self.db.executemany(
            "INSERT INTO memories VALUES "
            "(:id,:content,:type,:user,:agent,:session,:speaker,:source_id,:authority,"
            ":happened_at,:valid_from,:valid_to,:recorded_at,:invalid_at,:superseded_by,:confidence,:salience,"
            ":tier,:access_count,:entities,:derived_from)",
            [self._row(m) for m in memories],
        )
        self.db.commit()
        return len(memories)

    def clear(self) -> None:
        self.db.execute("DELETE FROM memories")
        self.db.commit()

    # --- reads -----------------------------------------------------------
    def all(self) -> list[Memory]:
        return self._query("SELECT * FROM memories")

    def live(self) -> list[Memory]:
        return self._query("SELECT * FROM memories WHERE invalid_at IS NULL")

    def eligible(self, scope: Scope, retrievable_only: bool = True) -> list[Memory]:
        """The three filters as one indexed query, instead of a full scan."""
        sql = "SELECT * FROM memories WHERE user = ? AND invalid_at IS NULL"
        params: list[object] = [scope.user]
        if scope.agent:
            sql += " AND (agent IS NULL OR agent = ?)"
            params.append(scope.agent)
        if retrievable_only:
            sql += " AND tier = ?"
            params.append(Tier.LONG_TERM.value)
        return self._query(sql, params)

    def search_text(self, term: str, scope: Scope) -> list[Memory]:
        """Exact-term lookup. Complements the vector index rather than replacing it."""
        return self._query(
            "SELECT * FROM memories WHERE user = ? AND invalid_at IS NULL "
            "AND content LIKE ?",
            [scope.user, f"%{term}%"],
        )

    # --- internals -------------------------------------------------------
    def _count(self) -> int:
        return self.db.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    def _query(self, sql: str, params: list | None = None) -> list[Memory]:
        rows = self.db.execute(sql, params or []).fetchall()
        self.scanned += len(rows)
        return [self._memory(r) for r in rows]

    @staticmethod
    def _row(m: Memory) -> dict:
        return {
            "id": m.id, "content": m.content, "type": m.type.value,
            "user": m.scope.user, "agent": m.scope.agent, "session": m.scope.session,
            "speaker": m.provenance.speaker, "source_id": m.provenance.source_id,
            "authority": m.provenance.authority,
            "happened_at": m.happened_at.isoformat() if m.happened_at else None,
            "valid_from": m.valid_from.isoformat() if m.valid_from else None,
            "valid_to": m.valid_to.isoformat() if m.valid_to else None,
            "recorded_at": m.recorded_at.isoformat(),
            "invalid_at": m.invalid_at.isoformat() if m.invalid_at else None,
            "superseded_by": m.superseded_by, "confidence": m.confidence,
            "salience": m.salience, "tier": m.tier.value,
            "access_count": m.access_count,
            "entities": json.dumps(list(m.entities)),
            "derived_from": json.dumps(list(m.derived_from)),
        }

    @staticmethod
    def _memory(r: sqlite3.Row) -> Memory:
        return Memory(
            content=r["content"], type=MemoryType(r["type"]),
            scope=Scope(user=r["user"], agent=r["agent"], session=r["session"]),
            provenance=Provenance(source_id=r["source_id"], speaker=r["speaker"],
                                  authority=r["authority"]),
            happened_at=_dt(r["happened_at"]), recorded_at=_dt(r["recorded_at"]),
            valid_from=_dt(r["valid_from"]), valid_to=_dt(r["valid_to"]),
            invalid_at=_dt(r["invalid_at"]), superseded_by=r["superseded_by"],
            confidence=r["confidence"], salience=r["salience"],
            tier=Tier(r["tier"]), access_count=r["access_count"],
            entities=tuple(json.loads(r["entities"])),
            derived_from=tuple(json.loads(r["derived_from"])),
            id=r["id"],
        )
