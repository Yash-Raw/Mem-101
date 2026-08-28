---
id: procedural-retrieval
title: "Procedural Retrieval"
kind: concept
stage: retrieve
contrasts_with: [hybrid-ranking]
related: [procedural-memory, step-order, temporal-routing]
status: published
---

# Procedural Retrieval

Finding a workflow: a separate index, a separate trigger, and an injection point that refuses to trim.

## Why it matters in a memory layer

Similarity assumes the candidates are interchangeable in kind. Facts and workflows are not — a fact is a short assertion, a procedure is a long sequence, and **length is a penalty on every similarity metric anyone ships**. On this course's corpus the four-step recipe never enters the top five, and the phrasing that returns anything returns a one-line comment about the recipe instead.

Nothing in the ranker is malfunctioning. It answers a question about similarity correctly, and similarity was the wrong question to ask about a workflow.

The injection point matters as much as the index. Every other memory type degrades gracefully under a token budget — three of four diet facts still answers the question. A procedure missing its fourth step is not shorter, it is wrong, and it looks exactly like a complete one.

## Connections

<!-- graph:begin -->
**Taught in:** [Retrieving Procedures](../curriculum/advanced/retrieving-procedures/index.md)

**Do not confuse with:** [Hybrid Ranking](hybrid-ranking.md)
<!-- graph:end -->
