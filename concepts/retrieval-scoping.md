---
id: retrieval-scoping
title: "Retrieval Scoping"
kind: concept
stage: retrieve
contrasts_with: [vector-search]
related: [read-path]
status: published
---

# Retrieval Scoping

Filtering candidates by hard, non-negotiable keys — owner, agent, memory type, validity window — *before* anything is ranked.

## Why it matters in a memory layer

Scope is a correctness boundary, not a performance optimisation. Ranking across users and trusting similarity to keep them apart is how memory systems leak between tenants, and the failure is silent: the wrong person's fact simply scores well. Filter first, always.

## Connections

<!-- graph:begin -->
**Taught in:** [Retrieval Is Not Enough](../curriculum/beginner/retrieval-is-not-enough/index.md)

**Used in:** [Three Temporal Questions](../curriculum/advanced/temporal-questions/index.md) · [Getting Memories Into the Prompt](../curriculum/beginner/context-assembly-v0/index.md) · [Watching It Fail](../curriculum/beginner/watching-it-fail/index.md) · [The Underrated Default](../curriculum/intermediate/relational-stores/index.md) · [Scope, Then Rank](../curriculum/intermediate/scope-then-rank/index.md) · [Scopes and Namespaces](../curriculum/intermediate/scopes-and-namespaces/index.md)

**Do not confuse with:** [Vector Search](vector-search.md)
<!-- graph:end -->
