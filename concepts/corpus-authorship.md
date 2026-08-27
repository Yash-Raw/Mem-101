---
id: corpus-authorship
title: "Corpus Authorship"
kind: concept
stage: orientation
contrasts_with: []
related: [write-path,memory-lifecycle]
status: published
---

# Corpus Authorship

Who wrote the body of text being searched. In retrieval, someone else did: documents, tickets, a wiki. In a memory layer, **the system writes its own corpus** as a byproduct of interacting.

An authored corpus is small, mutable, contradictory, and about one person. A given corpus is large, static, internally consistent, and about a domain.

## Why it matters in a memory layer

Nearly every design difference follows from this one distinction. A given corpus is chunked because it is too big; an authored corpus is extracted because raw turns are the wrong unit. A given corpus is versioned by re-ingestion; an authored corpus mutates in place and needs an audit trail. Getting this backwards produces a RAG pipeline with a user_id column and calling it memory.

## Connections

<!-- graph:begin -->
**Taught in:** [Memory Is Not RAG](../curriculum/beginner/memory-is-not-rag/index.md)
<!-- graph:end -->
