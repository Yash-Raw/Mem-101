---
id: derivation-graph
title: "Derivation Graph"
kind: concept
stage: store
contrasts_with: [graph-traversal]
related: [cascade-invalidation, provenance, supersession]
status: published
---

# Derivation Graph

The edges `derived_from` leaves behind: every summary, merge and corroboration points back at the memories it was built from.

## Why it matters in a memory layer

It is the graph nobody designs and every store has. A retrieval index is a pure function of its corpus, so deleting a document removes everything derived from it by construction; a memory store writes conclusions back next to their evidence, and retiring the evidence leaves the conclusion standing at full confidence.

Two things make it hard to audit. References must be in one namespace — this course's store wrote memory ids in one place and source ids in another, and a traversal that silently skips what it cannot resolve reports the same clean result as one that found nothing wrong. And a healthy derived fact *always* has a retired source: merging retires the loser and hands its evidence to the winner, so "every source retired" is the signature of normal consolidation, not of a broken chain.

## Connections

<!-- graph:begin -->
**Taught in:** [Temporal Knowledge Graphs](../curriculum/advanced/temporal-knowledge-graphs/index.md)

**Used in:** [Deletion That Actually Deletes](../curriculum/advanced/deletion-that-actually-deletes/index.md) · [Memory Observability](../curriculum/advanced/memory-observability/index.md)

**Do not confuse with:** [Graph Traversal](graph-traversal.md)
<!-- graph:end -->
