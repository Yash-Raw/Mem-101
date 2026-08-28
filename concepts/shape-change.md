---
id: shape-change
title: "Shape Change"
kind: concept
stage: store
contrasts_with: [backfill]
related: [memory-record, bi-temporal-modeling, deduplication]
status: published
---

# Shape Change

Adding to the record while the store is full and something depends on every record in it.

## Why it matters in a memory layer

Changing an index schema means re-indexing: the corpus is untouched, the old index is disposable, and the result is correct by construction. A memory store's records **are** the data, so every old record must stay readable and every reference to it must keep resolving.

Four properties made this course's mid-course migration safe, and only one of them could not have been arranged at migration time: **the id hashes identity, not state**. `Memory.id` covers user, type, content and source — so adding two nullable columns moved no id. Had it covered every field, all 37 ids would have changed on a modification that altered no content, breaking `derived_from`, `superseded_by`, the vector cache and every pinned assertion at once.

That decision was made in Beginner, for deduplication. This is the third unrelated thing it has paid for.

Add rather than rename. A rename is content-neutral and breaks every quoted number — the most expensive kind of change, because no behaviour moves and everything fails.

## Connections

<!-- graph:begin -->
**Taught in:** [Migrating Live Memory](../curriculum/advanced/schema-migration-on-live-memory/index.md)

**Do not confuse with:** [Backfill](backfill.md)
<!-- graph:end -->
