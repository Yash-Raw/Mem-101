---
id: coreference
title: "Coreference"
kind: concept
stage: extract
contrasts_with: []
related: [canonical-entity,entity-resolution]
status: published
---

# Coreference

Resolving a reference that names nobody — a pronoun, or a bare descriptor — to the entity it actually points at. "She works nights most of the month" is a fact about a specific person, and the record does not contain her name.

## Why it matters in a memory layer

A memory stored with an unresolved pronoun is attached to nobody and can never be retrieved by anyone. It is worse than a missing memory, because it occupies budget and looks well-formed. Resolution usually has to reach outside the record — to the turn before it, or the session it came from — which is why extraction alone cannot fix it.

## Connections

<!-- graph:begin -->
**Taught in:** [Entities and Aliases](../curriculum/intermediate/entities-and-aliases/index.md)

**Used in:** [Entity Resolution](../curriculum/intermediate/entity-resolution/index.md) · [The Query Is Not the Last Message](../curriculum/intermediate/query-formulation/index.md)
<!-- graph:end -->
