---
id: token-reservation
title: "Token Reservation"
kind: concept
stage: assemble
contrasts_with: []
related: [context-assembly,token-budget,score-fusion]
status: published
---

# Token Reservation

Guaranteeing each sub-question a share of the context, so a compound query's better-matching half cannot spend the whole budget on itself.

## Why it matters in a memory layer

It is the same argument [score fusion](score-fusion.md) makes about slots, one level down: ranking orders *within* a question and something has to allocate *between* them. On this corpus the guarantee turns out to be inherited — the retrieval merge already gives each sub-question its best answer — which leaves the interesting problem as **padding**: a second answer to a question already answered, spending tokens the other question still needs.

## Connections

<!-- graph:begin -->
**Taught in:** [The Packing Problem](../curriculum/intermediate/the-packing-problem/index.md)

**Used in:** [What Must Never Be Dropped](../curriculum/intermediate/compaction-safety/index.md) · [Ordering and Formatting](../curriculum/intermediate/ordering-and-formatting/index.md) · [Does This Earn Its Tokens?](../curriculum/intermediate/slot-value/index.md)
<!-- graph:end -->
