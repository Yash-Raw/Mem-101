---
id: token-budget
title: "Token Budget"
kind: concept
stage: assemble
contrasts_with: []
related: [context-window,context-assembly]
status: published
---

# Token Budget

The share of the context window allocated to recalled memories, after the system prompt, tools, and conversation have taken theirs. Typically a few hundred tokens for something that may hold thousands of facts.

## Why it matters in a memory layer

The budget is what turns retrieval into a *selection* problem. With room for six memories out of thirty-six, ranking stops being a nicety and becomes the whole game — and it is why measuring whether a memory earned its slot matters more than raising k.

## Connections

<!-- graph:begin -->
**Taught in:** [Context Is Not Memory](../curriculum/beginner/context-is-not-memory/index.md)

**Used in:** [Getting Memories Into the Prompt](../curriculum/beginner/context-assembly-v0/index.md)
<!-- graph:end -->
