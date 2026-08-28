---
id: composite-belief
title: "Composite Belief"
kind: concept
stage: evolve
contrasts_with: [element-cost]
related: [reflection, token-budget, derivation-graph]
status: published
---

# Composite Belief

One memory standing for several — composed from its members by template, with every source in `derived_from` so it can be checked and cascaded.

## Why it matters in a memory layer

Composition is what makes a derived belief auditable: it can be read back against its members, where a generated sentence has no route to the evidence.

It is also, on a budgeted context, a worse unit than the facts it replaces. The packer selects whole memories, so four atomic diet facts let it keep three and drop the one the question does not need; a composite is all-or-nothing and costs more than the useful subset. Measured here, the lowest passing budget goes from **51 to 55** when composites join their sources and **to 56** when they retire them — worse both ways.

The condition under which it pays is retrieval, not assembly: a store large enough that the atoms never rank together, where one composite that always ranks beats four that individually do not.

## Connections

<!-- graph:begin -->
**Taught in:** [Reflection and Insight](../curriculum/advanced/reflection-and-insight/index.md)

**Do not confuse with:** [Element Cost](element-cost.md)
<!-- graph:end -->
