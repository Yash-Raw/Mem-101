---
id: eviction
title: "Eviction"
kind: concept
stage: evolve
contrasts_with: []
related: [salience,supersession,memory-promotion]
status: published
---

# Eviction

Removing a memory from default retrieval when it stops earning its slot — by **demoting its tier**, never by deleting it.

## Why it matters in a memory layer

The distinction is the same one supersession makes and for the same reason: a faded memory is not false, nobody contradicted it, and the store holds the only copy. Demotion keeps it reachable by an explicit historical query and recoverable if it matters again; deletion throws away something still true on the strength of a heuristic. The cap belongs on the retrievable tier rather than on the store, because that is what actually costs — long-term memories are what every query scans and what competes for the token budget.

## Connections

<!-- graph:begin -->
**Taught in:** [Forgetting Under a Budget](../curriculum/intermediate/budgeted-forgetting/index.md)
<!-- graph:end -->
