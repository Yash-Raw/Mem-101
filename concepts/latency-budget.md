---
id: latency-budget
title: "Latency Budget"
kind: concept
stage: govern
contrasts_with: [cost-profile]
related: [critical-path, sleep-time-compute, consistency-window]
status: published
---

# Latency Budget

How much of the per-turn work has to finish before the next turn, and how much can wait.

## Why it matters in a memory layer

A retrieval system spends its budget at read time with the user watching, and indexing latency is nearly free to trade away. Here the model calls are on the **write** path — and the user is waiting for that too, because the next turn is answered from what this one stored. The deadline is *"before the next question"* rather than *"before the answer"*, which is more forgiving and is the whole reason deferral is available.

Classify by asking what breaks if a stage waits one turn. A memory not extracted **cannot be retrieved**; a duplicate is retrievable and merely wasteful; a summary that does not exist is read by nothing.

The result inverts the stage names. Consolidation is the pass over the whole store and it is deferrable; extraction is one call per turn and it is **81% of the blocking cost**. So the room to move work off the turn is 19%, and effort spent making extraction cheaper has no such ceiling.

## Connections

<!-- graph:begin -->
**Taught in:** [The Latency Budget](../curriculum/advanced/latency-budget/index.md)

**Used in:** [Caching, Batching, Routing](../curriculum/advanced/caching-batching-routing/index.md)

**Do not confuse with:** [Cost Profile](cost-profile.md)
<!-- graph:end -->
