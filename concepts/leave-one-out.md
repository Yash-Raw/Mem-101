---
id: leave-one-out
title: "Leave-One-Out"
kind: concept
stage: govern
contrasts_with: [store-invariant]
related: [store-invariant, write-authorisation, growth-curve]
status: published
---

# Leave-One-Out

Comparing each record against an aggregate of **the others**, so an outlier cannot move the standard it is measured against.

## Why it matters in a memory layer

The obvious clock invariant — *no memory is dated past the store's newest event* — cannot fail. A future-dated write **is** the newest event, so it passes its own check, and this course measured exactly that: the record the write policy refuses at the boundary sailed through the invariant meant to catch it at rest.

Comparing against the newest of the others catches it. The general form is that any invariant using an aggregate of the data cannot detect a record that shifts that aggregate — and the failure compounds, because two outliers validate each other.

It is also the argument that a boundary control and an invariant are not redundant. One refuses; the other notices what got in another way.

## Connections

<!-- graph:begin -->
**Taught in:** [Invariants and Drift Detection](../curriculum/advanced/invariants-and-drift-detection/index.md)

**Do not confuse with:** [Store Invariant](store-invariant.md)
<!-- graph:end -->
