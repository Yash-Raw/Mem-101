---
id: event-time
title: "Event Time vs Ingestion Time"
kind: concept
stage: store
contrasts_with: []
related: [memory-record,episodic-memory]
status: published
---

# Event Time vs Ingestion Time

Two different clocks. **Event time** is when a fact was true in the world; **ingestion time** is when the system learned it. They routinely differ, and sometimes in the same sentence.

## Why it matters in a memory layer

One timestamp is a bug you cannot fix retroactively. "Before the move I used to cycle to work" arrives in 2026 and is about 2025 — collapse the two clocks and the system believes she cycles now. Recording both is nearly free at write time and impossible to reconstruct afterwards.

## Connections

<!-- graph:begin -->
**Taught in:** [Designing the Memory Record](../curriculum/beginner/the-memory-record/index.md)
<!-- graph:end -->
