---
id: durability-gate
title: "The Durability Gate"
kind: concept
stage: extract
contrasts_with: [salience]
related: [extraction-pipeline,memory-promotion,over-extraction]
status: published
---

# The Durability Gate

A write-time filter asking whether a candidate deserves to outlive the session. Rules first — explicit markers, claim shape, imperatives — not a model call.

## Why it matters in a memory layer

Without one, every transient fact is embedded, ranked and competing for token budget forever, and the cost is per-retrieval rather than per-write. Distinct from [salience](salience.md): the gate is a boolean decision made once at write time with no usage history, while salience is a score that moves as a memory earns or loses its keep.

## Connections

<!-- graph:begin -->
**Taught in:** [Extraction Pipelines](../curriculum/intermediate/extraction-pipelines/index.md)

**Used in:** [Salience Scoring](../curriculum/intermediate/salience-scoring/index.md)

**Do not confuse with:** [Salience](salience.md)
<!-- graph:end -->
