---
id: write-path
title: "The Write Path"
kind: concept
stage: extract
contrasts_with: [read-path]
related: [memory-lifecycle,extraction]
status: published
---

# The Write Path

Everything a memory system does **between an interaction happening and a durable record existing**: deciding what was worth keeping, shaping it into a fact, reconciling it against what is already known, and choosing where it lives.

A retrieval system has no write path. Its corpus arrived already written.

## Why it matters in a memory layer

This is where memory systems are actually hard, and it is the part almost no tutorial covers. Retrieval quality is capped by write quality: no ranking function recovers a fact that was never extracted, and no reranker fixes a contradiction that was silently stored twice. Most "our memory is bad" bugs are write-path bugs surfacing at read time.

## Connections

<!-- graph:begin -->
**Taught in:** [Anatomy of a Memory Layer](../curriculum/beginner/anatomy-of-a-memory-layer/index.md) · [Memory Is Not RAG](../curriculum/beginner/memory-is-not-rag/index.md)

**Used in:** [Naive Extraction](../curriculum/beginner/naive-extraction/index.md)

**Do not confuse with:** [The Read Path](read-path.md)
<!-- graph:end -->
