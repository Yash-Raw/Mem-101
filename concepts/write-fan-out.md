---
id: write-fan-out
title: "Write Fan-Out"
kind: concept
stage: store
contrasts_with: []
related: [indexed-predicate,graph-traversal,supersession]
status: published
---

# Write Fan-Out

One logical write landing in several stores — a row, a vector, a set of graph edges — and the consistency problem that creates.

## Why it matters in a memory layer

The textbook hybrid architecture is drawn as three specialists, each better at its job than the others, and it leaves out that one **supersession** must now be reflected in all three or the system holds a belief in one place and its retraction in another. That is a correctness cost, not a performance one, and it is the reason to stay on a single store until the pressure is real. A hybrid store that is never checked for divergence is three stores that have quietly stopped describing the same world.

## Connections

<!-- graph:begin -->
**Taught in:** [Hybrid Architecture](../curriculum/intermediate/hybrid-architecture/index.md)
<!-- graph:end -->
