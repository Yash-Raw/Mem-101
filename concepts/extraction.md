---
id: extraction
title: "Extraction"
kind: concept
stage: extract
contrasts_with: []
related: [atomic-fact,over-extraction,write-path]
status: published
---

# Extraction

Turning raw interaction into addressable facts: deciding what in a turn is durable, and rewriting it as a standalone statement that can be retrieved and later updated.

## Why it matters in a memory layer

This is the stage retrieval systems do not have, and the one that caps everything downstream — no ranking function recovers a fact that was never extracted. It is also where the event/state mismatch is fixed: "I'm starting at Calico in January" is unretrievable by "where do I work" until extraction normalises it into a state.

## Connections

<!-- graph:begin -->
**Taught in:** [Naive Extraction](../curriculum/beginner/naive-extraction/index.md)

**Used in:** [Session Memory vs Long-Term Memory](../curriculum/beginner/session-vs-longterm/index.md) · [Writing Memories Down](../curriculum/beginner/writing-memories-down/index.md) · [Extraction Pipelines](../curriculum/intermediate/extraction-pipelines/index.md)
<!-- graph:end -->
