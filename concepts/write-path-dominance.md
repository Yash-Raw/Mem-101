---
id: write-path-dominance
title: "Write-Path Dominance"
kind: concept
stage: govern
contrasts_with: [cost-profile]
related: [extraction-pipeline, sleep-time-compute, memory-promotion]
status: published
---

# Write-Path Dominance

Indexing is per turn and forever; the query is nearly free — which inverts every cost intuition carried over from retrieval.

## Why it matters in a memory layer

Every message costs **two model calls** whether or not anyone ever asks a question about it, and that figure is linear in conversation length and **independent of how much has been remembered**. A year of use is arithmetic on message volume.

So the optimisation advice inverts too. Caching queries buys nothing when the read path makes no model calls; a cheaper extractor is the whole game; and deferring consolidation off the turn is worth measuring precisely because the expensive work is the work nobody is waiting for.

The read path being free is a design outcome rather than an optimisation. Arbitration refuses a model for explainability, ranking uses arithmetic for determinism, packing counts tokens because a budget is arithmetic — each argued on correctness grounds, with the cost profile as a side effect.

## Connections

<!-- graph:begin -->
**Taught in:** [The Write Path Dominates](../curriculum/advanced/cost-model/index.md)

**Do not confuse with:** [Cost Profile](cost-profile.md)
<!-- graph:end -->
