---
id: tombstone
title: "Tombstone"
kind: concept
stage: store
contrasts_with: [supersession]
related: [vector-index,supersession,eviction]
status: published
---

# Tombstone

A marker that a record still exists but must not be served — kept in the index rather than removed from it.

## Why it matters in a memory layer

Deleting a retired memory's vector would make audit and as-of queries impossible, and the course's whole spine is supersede-never-destroy. But leaving it silently retrievable is worse: the vector is still an accurate embedding of text that is no longer believed. A tombstone separates *is this a correct vector* from *should anyone see this*, which are different questions that a content-addressed cache cannot tell apart on its own. The same shape appears in [eviction](eviction.md), where a demoted memory stays in the log and out of default retrieval.

## Connections

<!-- graph:begin -->
**Taught in:** [Vector Stores for Data That Changes](../curriculum/intermediate/vector-stores-for-mutable-data/index.md)

**Do not confuse with:** [Supersession](supersession.md)
<!-- graph:end -->
