---
id: vector-index
title: "Vector Index"
kind: concept
stage: store
contrasts_with: [vector-search]
related: [tombstone,memory-record,idempotency]
status: published
---

# Vector Index

A stored embedding per memory, computed once and reused, rather than recomputed on every query.

## Why it matters in a memory layer

Without one, retrieval embeds every memory on every query — measured here, **2N calls per query**, 1,480 of them on a 740-memory store, for content that never changes. What makes it safe is that `Memory.id` is content-addressed: an edited memory is a different id and therefore a different cache entry, so a cached vector can never describe text it does not match. What makes it *interesting* is what the cache cannot see — a superseded belief keeps its id and its content, so its vector stays perfectly valid for something nobody should retrieve.

## Connections

<!-- graph:begin -->
**Taught in:** [Vector Stores for Data That Changes](../curriculum/intermediate/vector-stores-for-mutable-data/index.md)

**Used in:** [Hybrid Architecture](../curriculum/intermediate/hybrid-architecture/index.md) · [The Underrated Default](../curriculum/intermediate/relational-stores/index.md)

**Do not confuse with:** [Vector Search](vector-search.md)
<!-- graph:end -->
