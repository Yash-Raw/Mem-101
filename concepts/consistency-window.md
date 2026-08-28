---
id: consistency-window
title: "Consistency Window"
kind: concept
stage: evolve
contrasts_with: [sleep-time-compute]
related: [deduplication, supersession, slot]
status: published
---

# Consistency Window

The span between a fact arriving and the store agreeing with it — during which the system actively believes something already contradicted.

## Why it matters in a memory layer

It is the real price of deferred work, and it is not paid in compute. A store that converges to the right answer has a property nobody experiences, because the store is queried *during* the run.

Closing it does not require consolidating every turn. The window only opens when a turn claims a **slot** something live already claims, so gating on that runs consolidation on **11 turns instead of 25** for the same zero wrong answers. The gate needs no analysis of its own — `slot_of` is computed by the write path a moment later either way, and free is what lets a scheduler run on the critical path.

The failure mode to watch is a gate that half-works: pass the store *after* the turn's writes and a turn is contested by itself, taking 11 runs to 18 with identical output. A gate that fails completely shows up in a cost graph; one that half-fails reads as a gate that works.

## Connections

<!-- graph:begin -->
**Taught in:** [Sleep-Time Compute](../curriculum/advanced/sleep-time-compute/index.md)

**Do not confuse with:** [Sleep-Time Compute](sleep-time-compute.md)
<!-- graph:end -->
