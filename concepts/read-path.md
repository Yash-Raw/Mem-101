---
id: read-path
title: "The Read Path"
kind: concept
stage: retrieve
contrasts_with: [write-path]
related: [retrieval-scoping,context-assembly]
status: published
---

# The Read Path

Everything between a query arriving and relevant memories sitting in the model's context: scoping to an owner, ranking candidates, and packing the survivors into a token budget.

This is the whole of a RAG pipeline, and roughly a fifth of a memory layer.

## Why it matters in a memory layer

The read path is where memory looks most like retrieval, which is exactly why it is the part people over-invest in. It is genuinely important -- but a perfect read path over a corrupted store returns corruption faster.

## Connections

<!-- graph:begin -->
**Taught in:** [Anatomy of a Memory Layer](../curriculum/beginner/anatomy-of-a-memory-layer/index.md) · [Memory Is Not RAG](../curriculum/beginner/memory-is-not-rag/index.md)

**Used in:** [Embedding Recall](../curriculum/beginner/embedding-recall/index.md) · [Retrieval Is Not Enough](../curriculum/beginner/retrieval-is-not-enough/index.md)

**Do not confuse with:** [The Write Path](write-path.md)
<!-- graph:end -->
