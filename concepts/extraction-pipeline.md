---
id: extraction-pipeline
title: "The Extraction Pipeline"
kind: concept
stage: extract
contrasts_with: []
related: [extraction,durability-gate,atomic-fact]
status: published
---

# The Extraction Pipeline

Extraction as stages rather than one prompt: generate candidates, atomise them, gate for durability, route by type. Each stage has a single job and can be tested alone.

## Why it matters in a memory layer

One prompt doing four jobs cannot be debugged — when a fact is missing you cannot tell whether it was never proposed, was merged into another, was filtered, or was mistyped. Staging also decides where cost lives: the candidate step is the only one that needs a model, so keeping the rest deterministic makes the write path cheap and auditable.

## Connections

<!-- graph:begin -->
**Taught in:** [Extraction Pipelines](../curriculum/intermediate/extraction-pipelines/index.md)

**Used in:** [Learning From Outcomes](../curriculum/advanced/learning-from-outcomes/index.md) · [Procedural Memory](../curriculum/advanced/procedural-memory/index.md) · [Atomic Memories](../curriculum/intermediate/atomic-memories/index.md) · [Entities and Aliases](../curriculum/intermediate/entities-and-aliases/index.md) · [Precision and Recall on the Write Path](../curriculum/intermediate/extraction-quality/index.md)
<!-- graph:end -->
