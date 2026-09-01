---
id: rollback
title: "Rollback"
kind: concept
stage: evolve
contrasts_with: [cascade-deletion]
related: [staged-change, supersession, derivation-graph]
status: published
---

# Rollback

Undoing an applied consolidation: drop what it added, revive what it retired.

## Why it matters in a memory layer

An index is reversible by construction — the corpus is untouched, so a bad index is fixed by building another. A memory store has no corpus behind it, so undo is something you design or something you do not have.

It works here for one reason: retirement sets `invalid_at` and `superseded_by` on records that stay in the log. Undo is clearing two fields and dropping the added memories, and the store comes back identical — ids, validity, supersession pointers, tiers. A store that had deleted the eight subsumed beliefs could not do this at all, and no amount of care in the rollback function recovers information that is gone.

**Undo is a property of the write model, not of the undo function** — which is what `supersession-not-deletion` was buying two levels earlier.

## Connections

<!-- graph:begin -->
**Taught in:** [Promotion as a Release](../curriculum/advanced/promotion-as-release/index.md)

**Do not confuse with:** [Cascade Deletion](cascade-deletion.md)
<!-- graph:end -->
