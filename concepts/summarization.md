---
id: summarization
title: "Summarization"
kind: concept
stage: evolve
contrasts_with: [deduplication]
related: [derived-memory,token-budget]
status: published
---

# Summarization

Compressing many memories into fewer, so a long history fits a budget that does not grow.

## Why it matters in a memory layer

Compression only comes from what you decline to carry forward — a summary that keeps every claim is longer than its parts, because of the joining. So the real design question is not how to summarise but **what to drop**, and the answer has to be defensible: dropping episodes keeps the standing beliefs and loses the timestamps that made the episodes worth having. An extractive summary buys traceability, since every sentence in it exists in the store and can be attributed; a generative one buys fluency and pays in provenance.

## Connections

<!-- graph:begin -->
**Taught in:** [Summarization and Compaction](../curriculum/intermediate/summarization-and-compaction/index.md)

**Used in:** [Semantic Drift](../curriculum/intermediate/semantic-drift/index.md)

**Do not confuse with:** [Deduplication](deduplication.md)
<!-- graph:end -->
