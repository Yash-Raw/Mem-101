---
id: vector-search
title: "Vector Search"
kind: concept
stage: retrieve
contrasts_with: []
related: [retrieval-scoping,read-path]
status: published
---

# Vector Search

Embedding text into a vector space and ranking by geometric closeness, usually cosine similarity.

## Why it matters in a memory layer

It is a genuinely good tool for the read path and a genuinely bad proxy for relevance in a memory layer. Similarity has no opinion about recency, authority, or whether a fact has been retired, so it will confidently rank a dead belief above a live one. It answers "what looks like this", never "what is true".

## Connections

<!-- graph:begin -->
**Taught in:** [Embedding Recall](../curriculum/beginner/embedding-recall/index.md)

**Used in:** [Retrieval Is Not Enough](../curriculum/beginner/retrieval-is-not-enough/index.md) · [Watching It Fail](../curriculum/beginner/watching-it-fail/index.md) · [Your First Memory Layer](../curriculum/beginner/your-first-memory-layer/index.md) · [Deduplication](../curriculum/intermediate/deduplication/index.md)
<!-- graph:end -->
