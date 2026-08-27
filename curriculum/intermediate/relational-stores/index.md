---
id: relational-stores
title: "The Underrated Default"
level: intermediate
stage: store
estimated_minutes: 40
concepts_taught: [indexed-predicate]
concepts_required: [vector-index, retrieval-scoping, namespace]
lessons_required: [vector-stores-for-mutable-data]
capstone_piece: memlab.store.sqlite
lab: lab/lab.py
lab_runtime: fake
status: published
---

# The Underrated Default

> **In one line.** Three of the read path's four operations are `WHERE` clauses, and the store has been answering them by loading everything and throwing most of it away.

## Where this sits

<!-- graph:begin -->
**Stage:** `store` · **Level:** intermediate · **~40 min**

**You need first:** [Vector Stores for Data That Changes](../vector-stores-for-mutable-data/index.md)

**Concepts assumed:** [Vector Index](../../../concepts/vector-index.md) · [Retrieval Scoping](../../../concepts/retrieval-scoping.md) · [Namespace](../../../concepts/namespace.md)

**This unlocks:** [Graph Stores](../graph-stores/index.md)
<!-- graph:end -->

## The problem

Look at what `scope-then-rank` actually does:

```python
out = [m for m in memories if m.scope.matches(scope) and m.is_live]
out = [m for m in out if m.tier is Tier.LONG_TERM]
```

Load all 37, keep 18. Three predicates — owner, validity, tier — each an exact match on a field, evaluated in Python over the entire store. That is a full scan with the filter on the wrong side of the I/O.

It is invisible at 37 memories and it is the *shape* that matters: the cost is linear in everything ever written, for a query that wants a small indexed subset.

## Why this isn't RAG

"Memory layer" is often taken to mean "vector database", and the substitution is so common it goes unexamined. A document search system genuinely is dominated by similarity, because the only thing it knows about a chunk is its text.

A memory store knows a great deal more: who it belongs to, when it was true, whether it still is, what tier it sits in, what type of claim it is, what it was derived from. **Similarity is one column of that.** The others are exact-match and range predicates over structured fields — which is what relational databases have been good at for fifty years, and what a vector index is bad at.

## Mechanism

SQLite, from the standard library. No server, ACID writes, indexed predicates, and text search — and the three filters become one query:

```sql
SELECT * FROM memories
 WHERE user = ? AND invalid_at IS NULL AND tier = ?
```

with indexes on exactly those columns:

```sql
CREATE INDEX idx_scope    ON memories(user, agent);
CREATE INDEX idx_validity ON memories(invalid_at);
CREATE INDEX idx_tier     ON memories(tier);
```

The engine returns **18 rows**; the Python filter had to load **37** to produce the same answer. Both give an identical result — the lab asserts it — and only one of them stays flat as the store grows.

**`INSERT OR IGNORE` on a content-addressed primary key gives idempotency for free.** Re-inserting the whole store writes zero rows. The property Beginner designed into `Memory.id` for a completely different reason turns out to be exactly what a relational store wants for its key.

**Text search complements the vector index rather than competing.** `search_text('Calico')` returns both Calico memories exactly, including the episodic one similarity ranks poorly. `hybrid-ranking` already learned that exact-term matching catches what embeddings smear; this is where that lookup gets an index behind it.

## Design decisions

**SQLite, or Postgres?** SQLite here, and the point is that it is enough for longer than people expect: one file, no server, real transactions. The lesson is which *operations* belong in a relational store, and that answer does not change with the engine.

**Store `entities` and `derived_from` as JSON columns?** Yes, for now, and it is a real limitation — you cannot index into them, so "every memory mentioning Samira" is still a scan. The next lesson is about the store that does index that, and whether this corpus needs it.

**One store, or a relational store beside the vector index?** That is `hybrid-architecture`, two lessons on, and the honest answer is that a single relational store carrying a vector column handles more cases than the three-specialist diagram suggests.

## Lab

**You'll implement:** `eligible` as an indexed query, and `add` with idempotent inserts.

**Run:**
```
uv run python curriculum/intermediate/relational-stores/lab/lab.py
```

**Expected output:** 37 rows inserted, a second insert writing **0**, `all=37 live=30 eligible=18`, and the assertion that the SQL result is identical to the Python filter — with **18** rows returned against **37** loaded.

**Stretch:** drop the three indexes and re-run. On 37 rows nothing measurable changes, and `EXPLAIN QUERY PLAN` changes from a search to a scan. The plan is the signal; the timing will not tell you anything until it is far too late to fix cheaply.

## What this adds to the capstone

`memlab.store.sqlite` — `SqliteStore` implementing the same `add` / `all` / `live` / `replace` / `clear` interface as `JsonlStore`, plus `eligible` and `search_text`. Swappable, not parallel.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Query cost grows with total writes | Filters applied in application code | Compare rows loaded against rows used | Indexed predicates |
| Everything is a vector problem | Vector store treated as the memory store | List the read path's operations; count how many are similarity | A relational store for the rest |
| Re-ingest duplicates rows | Non-content-addressed primary key | Insert the same store twice | `INSERT OR IGNORE` on the id |
| Exact terms are unfindable | Only semantic search available | Search for a company name | Text search beside the vector index |
| "Memories mentioning X" is slow | Entity list stored as opaque JSON | Query by entity | An entity index — next lesson |

## Check yourself

??? question "The SQL and the Python filter return identical results. What is actually gained?"
    Where the work happens. Python loads 37 rows to keep 18; the query returns 18. Identical answers, and one of them stays flat as the store grows while the other is linear in everything ever written. At this size the difference is unmeasurable, which is exactly when it is cheap to fix.

??? question "Why does content-addressed `id` matter more here than it did in Beginner?"
    Because a primary key makes it structural. `INSERT OR IGNORE` turns idempotency from something the application remembers to do into something the store cannot violate — and re-ingestion after a replay or a bad deploy stops being a class of bug.

??? question "If a relational store handles most operations, why keep the vector index?"
    Because one operation genuinely is similarity, and no `WHERE` clause expresses it. The argument is not that vectors are unnecessary — it is that they are one column, and building the whole store around that column leaves the other five to application code.

## Connections

<!-- graph:begin -->
**Stage:** `store` · **Level:** intermediate · **~40 min**

**You need first:** [Vector Stores for Data That Changes](../vector-stores-for-mutable-data/index.md)

**Concepts assumed:** [Vector Index](../../../concepts/vector-index.md) · [Retrieval Scoping](../../../concepts/retrieval-scoping.md) · [Namespace](../../../concepts/namespace.md)

**This unlocks:** [Graph Stores](../graph-stores/index.md)
<!-- graph:end -->
