---
id: cost-profile
title: "Cost Profile"
kind: concept
stage: govern
contrasts_with: [write-path-dominance]
related: [vector-index, element-cost, extraction-pipeline]
status: published
---

# Cost Profile

Where a system's model calls actually happen, counted rather than assumed.

## Why it matters in a memory layer

A retrieval stack pays at read time — embed the query, search, rerank, often a call to synthesise — and indexing is a one-off amortised over every future query. That makes *"index once, query forever"* a sound way to think about the bill.

Measured here, the profile is inverted and starkly so: the full write path costs **48 model calls and 38 embeddings** over 24 turns, and one question costs **zero model calls and two embeddings**. Not cheap — none.

Count calls rather than seconds. Seconds belong to the machine and the provider; calls are what a bill is denominated in and do not change when the hardware does. And count by patching the client, because a counter added at each call site misses the one somebody wrote last week.

## Connections

<!-- graph:begin -->
**Taught in:** [The Write Path Dominates](../curriculum/advanced/cost-model/index.md)

**Used in:** [Caching, Batching, Routing](../curriculum/advanced/caching-batching-routing/index.md) · [The Latency Budget](../curriculum/advanced/latency-budget/index.md)

**Do not confuse with:** [Write-Path Dominance](write-path-dominance.md)
<!-- graph:end -->
