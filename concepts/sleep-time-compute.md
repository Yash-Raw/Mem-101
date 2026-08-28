---
id: sleep-time-compute
title: "Sleep-Time Compute"
kind: concept
stage: evolve
contrasts_with: [deduplication]
related: [consistency-window, slot, summarization]
status: published
---

# Sleep-Time Compute

Memory work moved off the turn — consolidation, summarisation, reflection — run between conversations rather than while someone is waiting.

## Why it matters in a memory layer

It is cheap and it is not free. On this course's corpus, deferring every consolidation to a single batch costs **38 embeddings against 503**, and reaches the identical store — consolidation is order-independent here, which is the property that makes deferral safe at all and is worth measuring rather than assuming.

What it costs is the window. Deferred, the store spends **11 of 24 turns** believing a job the user has already left, including the turn where they correct the assistant about it. Indexing late means a fact is missing; arbitrating late means the system argues.

## Connections

<!-- graph:begin -->
**Taught in:** [Sleep-Time Compute](../curriculum/advanced/sleep-time-compute/index.md)

**Used in:** [Background Job Mechanics](../curriculum/advanced/background-job-mechanics/index.md) · [The Latency Budget](../curriculum/advanced/latency-budget/index.md)

**Do not confuse with:** [Deduplication](deduplication.md)
<!-- graph:end -->
