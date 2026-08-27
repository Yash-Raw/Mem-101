---
id: write-path-recall
title: "Write-Path Recall"
kind: concept
stage: extract
contrasts_with: []
related: [extraction,event-vs-state,retrieval-scoping]
status: published
---

# Write-Path Recall

Whether a fact was ever written in a form a question can reach — measured separately from whether retrieval found it. Two different failures with the same symptom.

## Why it matters in a memory layer

Only one of those failures is fixable at read time, so conflating them sends you tuning a reranker for a bug that lives in extraction. Worth splitting further: *written* and *reachable* are also different. A state can exist in the store and still be unreachable because it was phrased in words no question would use, which scores full recall on any store-shaped check and answers nothing.

## Connections

<!-- graph:begin -->
**Taught in:** [Precision and Recall on the Write Path](../curriculum/intermediate/extraction-quality/index.md)
<!-- graph:end -->
