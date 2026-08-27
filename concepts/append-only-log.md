---
id: append-only-log
title: "The Append-Only Log"
kind: concept
stage: store
contrasts_with: []
related: [memory-record,provenance]
status: published
---

# The Append-Only Log

A store that only ever adds. Nothing is edited in place; corrections arrive as new entries that reference the old.

## Why it matters in a memory layer

It is the right first store and the right permanent substrate: durable, inspectable, and it makes provenance and audit free. Its limitation is the lesson — an append-only log cannot express "this is no longer true" without a second layer on top that knows which entries are live.

## Connections

<!-- graph:begin -->
**Taught in:** [Writing Memories Down](../curriculum/beginner/writing-memories-down/index.md)

**Used in:** [Embedding Recall](../curriculum/beginner/embedding-recall/index.md)
<!-- graph:end -->
