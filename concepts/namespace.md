---
id: namespace
title: "Namespace"
kind: concept
stage: store
contrasts_with: [retrieval-scoping]
related: [provenance]
status: published
---

# Namespace

The structured key a memory is filed under — user, agent, session — and the visibility rule that decides who may read it.

## Why it matters in a memory layer

This is the multi-tenancy substrate, and it is a correctness boundary rather than an index hint. Ranking across tenants and trusting similarity to keep them apart is how memory systems leak between users, and the failure is silent: nothing errors, the wrong person's fact simply scores well. Filter on structured keys first, rank second, and assert the leak set is empty rather than assuming it.

## Connections

<!-- graph:begin -->
**Taught in:** [Scopes and Namespaces](../curriculum/intermediate/scopes-and-namespaces/index.md)

**Used in:** [Scope, Then Rank](../curriculum/intermediate/scope-then-rank/index.md)

**Do not confuse with:** [Retrieval Scoping](retrieval-scoping.md)
<!-- graph:end -->
