---
id: indexed-predicate
title: "Indexed Predicates"
kind: concept
stage: store
contrasts_with: [vector-index]
related: [retrieval-scoping,namespace]
status: published
---

# Indexed Predicates

The hard filters — owner, validity, tier, type — expressed as indexed columns a database answers, rather than as a Python loop over everything.

## Why it matters in a memory layer

Most of what a memory store does is not similarity. Filtering by owner, excluding retired beliefs, restricting to a retrievable tier, ordering by event time: every one is a `WHERE` clause, and the read path currently answers them by loading the whole store and discarding most of it. "Memory layer" is often taken to mean "vector database", and the vector work is one column of the problem — the other columns are what a relational store has been good at for fifty years.

## Connections

<!-- graph:begin -->
**Taught in:** [The Underrated Default](../curriculum/intermediate/relational-stores/index.md)

**Used in:** [Graph Stores](../curriculum/intermediate/graph-stores/index.md) · [Hybrid Architecture](../curriculum/intermediate/hybrid-architecture/index.md)

**Do not confuse with:** [Vector Index](vector-index.md)
<!-- graph:end -->
