---
id: procedural-memory
title: "Procedural Memory"
kind: concept
stage: store
contrasts_with: [semantic-memory]
related: [step-order, extraction-pipeline, memory-record]
status: published
---

# Procedural Memory

How to do something — a workflow whose **order is part of its content**, not a set of independently retrievable facts.

## Why it matters in a memory layer

Atomisation is the write path's job: break statements into facts that can be retrieved on their own. It is exactly the wrong operation for a procedure. Four steps are not four facts, and a memory layer preserves their order only because the extractor was told to make an exception.

Retrieval never faced this. A document arrives whole and comes back whole, so a recipe's steps stay in sequence because nothing had the chance to reorder them.

The subtler problem is that a remark *about* a procedure gets the same type. On this course's corpus two memories are typed procedural and one is *"the diff step matters most"* — split it on commas and you get a well-formed two-step workflow that does not exist. Dropping it beats parsing it, because a wrong procedure is not noise; it is something someone might follow.

## Connections

<!-- graph:begin -->
**Taught in:** [Procedural Memory](../curriculum/advanced/procedural-memory/index.md) · [The Taxonomy That Actually Routes](../curriculum/beginner/memory-taxonomy/index.md)

**Used in:** [Resolving 'Last Week'](../curriculum/advanced/relative-time-resolution/index.md) · [Atomic Memories](../curriculum/intermediate/atomic-memories/index.md) · [The Typed Memory Model](../curriculum/intermediate/typed-memory-model/index.md)

**Do not confuse with:** [Semantic Memory](semantic-memory.md)
<!-- graph:end -->
