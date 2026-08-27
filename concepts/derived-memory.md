---
id: derived-memory
title: "Derived Memory"
kind: concept
stage: evolve
contrasts_with: []
related: [provenance,deduplication,semantic-drift]
status: published
---

# Derived Memory

A memory the system computed rather than extracted — a summary, a promoted belief, a merged record — carrying `derived_from`: the ids of everything it was built from.

## Why it matters in a memory layer

Without that link a derived memory is an orphan claim. You cannot rebuild it when a source changes, cannot trace why the system believes it, and cannot delete it when a source is deleted — which is the whole difficulty of the right to be forgotten: you removed the episode and the summary still knows. It is also what makes compaction repeatable, since re-deriving from anchors is idempotent where re-compressing the previous output is not.

## Connections

<!-- graph:begin -->
**Taught in:** [Summarization and Compaction](../curriculum/intermediate/summarization-and-compaction/index.md)

**Used in:** [Semantic Drift](../curriculum/intermediate/semantic-drift/index.md)
<!-- graph:end -->
