---
id: memory-staleness
title: "Staleness"
kind: concept
stage: evolve
contrasts_with: []
related: [belief-updating,semantic-memory]
status: published
---

# Staleness

A memory that was true when written and is not true now, and that nothing has marked as retired.

## Why it matters in a memory layer

Staleness is the characteristic memory-layer bug and it gets *worse* with good engineering: a fact stated early and reinforced often scores highly on both similarity and salience, so the more confident the system is, the more confidently it is wrong. It cannot be fixed on the read path.

## Connections

<!-- graph:begin -->
**Taught in:** [Watching It Fail](../curriculum/beginner/watching-it-fail/index.md)
<!-- graph:end -->
