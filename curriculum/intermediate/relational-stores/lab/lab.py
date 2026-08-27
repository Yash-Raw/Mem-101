"""Lab: three filters, one indexed query.

    uv run python curriculum/intermediate/relational-stores/lab/lab.py
"""
from __future__ import annotations

from memlab.store.sqlite import SqliteStore
from memlab.types import Memory, Scope, Tier


def eligible_sql(db: SqliteStore, scope: Scope, retrievable_only: bool = True) -> list[Memory]:
    """TODO: the three filters scope-then-rank applies in Python, as one query.

      owner     user = ?           (and agent, when scoped to one)
      validity  invalid_at IS NULL
      tier      tier = 'long_term'

    Use db._query so the row count is recorded for the comparison below.
    """
    raise NotImplementedError("implement eligible_sql")


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


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    source = JsonlStore("/tmp/memlab-sqlite-src.jsonl")
    source.clear()
    ingest(source, scope, at("I6"))
    memories = source.all()

    db = SqliteStore()
    print(f"inserted {db.add(memories)} rows; re-insert writes {db.add(memories)} (idempotent)")
    print(f"  all={len(db.all())}  live={len(db.live())}  eligible={len(eligible_sql(db, scope))}\n")

    result = compare_with_python(db, memories, scope)
    print(f"  identical result:      {result['same_result']}")
    print(f"  rows the query returns: {result['sql_rows_returned']}")
    print(f"  rows Python must load:  {result['python_rows_loaded']}\n")

    print("exact-term lookup for 'Calico':")
    for m in db.search_text("Calico", scope):
        print(f"   {m.content[:58]}")

    print("\nquery plan:")
    for line in query_plan(db, scope):
        print(f"   {line}")


if __name__ == "__main__":
    main()
