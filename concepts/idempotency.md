---
id: idempotency
title: "Idempotent Writes"
kind: concept
stage: store
contrasts_with: []
related: [memory-record,append-only-log]
status: published
---

# Idempotent Writes

Ingesting the same turn twice produces one memory, not two — usually by deriving the record's id from its content and source rather than from a counter.

## Why it matters in a memory layer

Re-ingestion is normal, not exceptional: retries, replays, backfills, a consolidation job that runs twice. Without content-addressed ids every one of those silently doubles the store, and duplicate facts then out-vote unique ones in retrieval.

## Connections

<!-- graph:begin -->
**Taught in:** [Writing Memories Down](../curriculum/beginner/writing-memories-down/index.md)

**Used in:** [Deduplication](../curriculum/intermediate/deduplication/index.md) · [Vector Stores for Data That Changes](../curriculum/intermediate/vector-stores-for-mutable-data/index.md)
<!-- graph:end -->
