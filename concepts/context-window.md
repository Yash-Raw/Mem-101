---
id: context-window
title: "The Context Window"
kind: concept
stage: assemble
contrasts_with: [working-memory]
related: [token-budget,context-assembly]
status: published
---

# The Context Window

The fixed number of tokens a model can attend to in one call. Everything the model knows in that moment is inside it; everything else does not exist.

## Why it matters in a memory layer

The window is a *budget*, not a memory. Enlarging it does not add selection, persistence, or the ability to change a belief — it only makes the same unsolved problems more expensive. Attention also degrades over long spans, so a fact buried mid-window is present but not necessarily used.

## Connections

<!-- graph:begin -->
**Taught in:** [Context Is Not Memory](../curriculum/beginner/context-is-not-memory/index.md)

**Do not confuse with:** [Working Memory](working-memory.md)
<!-- graph:end -->
