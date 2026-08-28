---
id: graph-traversal
title: "Graph Traversal"
kind: concept
stage: store
contrasts_with: [indexed-predicate]
related: [canonical-entity,entity-resolution]
status: published
---

# Graph Traversal

Following relations between entities instead of querying records one at a time — the operation a graph store exists to make cheap.

## Why it matters in a memory layer

It pays exactly when there are relations to follow, and recognising that you have none is worth more than adopting the architecture anyway. Built over this course's corpus, the entity graph has **one node and zero entity-to-entity edges**: the only traversal available is entity → its memories, which is a dictionary lookup wearing a graph's clothes. A store choice is a claim about the shape of your data, and the claim should be checked.

## Connections

<!-- graph:begin -->
**Taught in:** [Graph Stores](../curriculum/intermediate/graph-stores/index.md)

**Used in:** [Temporal Knowledge Graphs](../curriculum/advanced/temporal-knowledge-graphs/index.md) · [Hybrid Architecture](../curriculum/intermediate/hybrid-architecture/index.md)

**Do not confuse with:** [Indexed Predicates](indexed-predicate.md)
<!-- graph:end -->
