---
id: canonical-entity
title: "Canonical Entity"
kind: concept
stage: store
contrasts_with: []
related: [entity-resolution,coreference]
status: published
---

# Canonical Entity

The single identity that a cluster of surface forms resolves to, plus the id that names it. Every mention of the same person, place or thing carries that id, whatever words were actually used.

## Why it matters in a memory layer

It is the join key that makes accumulation possible: once six memories share `entities=('samira',)`, a question about that person can gather all six, and a contradiction between any two becomes detectable. The id has to be **stable** — derived from the whole cluster rather than from whichever form arrived first — or early records end up pointing at a name nothing else uses.

## Connections

<!-- graph:begin -->
**Taught in:** [Entity Resolution](../curriculum/intermediate/entity-resolution/index.md)

**Used in:** [Contradiction Detection](../curriculum/intermediate/contradiction-detection/index.md) · [Scopes and Namespaces](../curriculum/intermediate/scopes-and-namespaces/index.md)
<!-- graph:end -->
