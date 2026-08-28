---
id: critical-path
title: "Critical Path"
kind: concept
stage: govern
contrasts_with: [latency-budget]
related: [consistency-window, slot, sleep-time-compute]
status: published
---

# Critical Path

The stages that must complete before the next turn can be answered.

## Why it matters in a memory layer

Most stages are on it or off it as a property of the stage: extraction always blocks, summarisation never does. **Arbitration is the exception** — it blocks exactly when the turn claims a slot something live already claims, which is a property of the *turn*.

That single conditional is what makes deferral tunable at all. Gating on contested slots runs consolidation on 11 turns of 24 rather than all of them, costing 0.46 model calls per turn against extraction's 2.0, and closing the consistency window that deferring everything would leave open.

List the stages you decided **not** to run, too. A budget that omits them is one that silently regains them.

## Connections

<!-- graph:begin -->
**Taught in:** [The Latency Budget](../curriculum/advanced/latency-budget/index.md)

**Do not confuse with:** [Latency Budget](latency-budget.md)
<!-- graph:end -->
