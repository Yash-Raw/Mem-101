"""Reference solution."""
from __future__ import annotations

from memlab.store.sqlite import SqliteStore
from memlab.types import Memory, Scope, Tier


def eligible_sql(db: SqliteStore, scope: Scope, retrievable_only: bool = True) -> list[Memory]:
    sql = "SELECT * FROM memories WHERE user = ? AND invalid_at IS NULL"
    params: list[object] = [scope.user]
    if scope.agent:
        sql += " AND (agent IS NULL OR agent = ?)"
        params.append(scope.agent)
    if retrievable_only:
        sql += " AND tier = ?"
        params.append(Tier.LONG_TERM.value)
    return db._query(sql, params)


def compare_with_python(db: SqliteStore, memories: list[Memory], scope: Scope) -> dict:
    """Same answer, different amount of work."""
    from memlab.retrieve.scoped import eligible as python_filter

    db.scanned = 0
    rows = eligible_sql(db, scope)
    returned = db.scanned
    in_python = python_filter(memories, scope)
    return {
        "sql_rows_returned": returned,
        "python_rows_loaded": len(memories),
        "same_result": {m.id for m in rows} == {m.id for m in in_python},
        "kept": len(rows),
    }


def query_plan(db: SqliteStore, scope: Scope) -> list[str]:
    rows = db.db.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM memories "
        "WHERE user = ? AND invalid_at IS NULL AND tier = ?",
        [scope.user, Tier.LONG_TERM.value],
    ).fetchall()
    return [r["detail"] for r in rows]
