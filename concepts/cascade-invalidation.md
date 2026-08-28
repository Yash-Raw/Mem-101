---
id: cascade-invalidation
title: "Cascade Invalidation"
kind: concept
stage: evolve
contrasts_with: [supersession]
related: [derivation-graph, deletion, provenance]
status: published
---

# Cascade Invalidation

Propagating a retirement through everything derived from it, transitively, until nothing live is left standing on nothing.

## Why it matters in a memory layer

Supersession touches one record. Everything summarised, merged or inferred from it keeps its own `invalid_at` of `None` and its own confidence, and nothing in the read path can tell that its evidence is gone.

The propagation has to run to a fixed point, because retiring a derived fact can strand something derived from *it*. And it has to know which retirements were the derivation — a merge retires the loser *by* the winner, so a cascade that treats that as broken support deletes correct beliefs on its first pass.

Zero cascaded records is the correct outcome on a healthy store, which is exactly why it must be reported alongside the count of edges that could not be followed. Otherwise a working cascade and a disconnected one look identical.

## Connections

<!-- graph:begin -->
**Taught in:** [Temporal Knowledge Graphs](../curriculum/advanced/temporal-knowledge-graphs/index.md)

**Do not confuse with:** [Supersession](supersession.md)
<!-- graph:end -->
