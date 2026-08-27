---
id: semantic-drift
title: "Semantic Drift"
kind: concept
stage: evolve
contrasts_with: []
related: [summarization,derived-memory]
status: published
---

# Semantic Drift

The compounding loss from summarising a summary. Each round is lossy against a base that already shrank, so the decay is geometric rather than linear.

## Why it matters in a memory layer

It is the failure mode of the cheapest possible compaction loop — take yesterday's summary as today's input — and it is invisible, because the only record of what was lost was the input just replaced. Measured on this course's corpus, four naive rounds retain 19% of the original claims where re-deriving from anchors holds steady at 70%. The fix is not a better summariser; it is never summarising a summary.

## Connections

<!-- graph:begin -->
**Taught in:** [Semantic Drift](../curriculum/intermediate/semantic-drift/index.md)

**Used in:** [From Episode to Belief](../curriculum/intermediate/episodic-to-semantic/index.md)
<!-- graph:end -->
