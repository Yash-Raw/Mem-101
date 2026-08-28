---
id: memory-record
title: "The Memory Record"
kind: concept
stage: store
contrasts_with: []
related: [provenance,event-time,semantic-memory]
status: published
---

# The Memory Record

The unit a memory layer stores: content, type, scope, provenance, timestamps, confidence, salience. Not a chunk of text — an addressable, updatable object.

## Why it matters in a memory layer

The fields chosen here decide what is possible later. Without two clocks you cannot answer "what did I believe then"; without provenance you cannot honour a deletion request, because nothing identifies what to delete; without a validity field you can only delete, never retire. Almost every Level 2 mechanism is a field on this record.

## Connections

<!-- graph:begin -->
**Taught in:** [Designing the Memory Record](../curriculum/beginner/the-memory-record/index.md)

**Used in:** [PII on the Write Path](../curriculum/advanced/pii-on-the-write-path/index.md) · [Procedural Memory](../curriculum/advanced/procedural-memory/index.md) · [Regression Testing a Stateful System](../curriculum/advanced/regression-testing-state/index.md) · [Proving You Forgot](../curriculum/advanced/rtbf-and-auditability/index.md) · [Two Clocks](../curriculum/advanced/two-clocks/index.md) · [Why Memory Eval Is Hard](../curriculum/advanced/why-memory-eval-is-hard/index.md) · [Naive Extraction](../curriculum/beginner/naive-extraction/index.md) · [Writing Memories Down](../curriculum/beginner/writing-memories-down/index.md) · [The Typed Memory Model](../curriculum/intermediate/typed-memory-model/index.md)
<!-- graph:end -->
