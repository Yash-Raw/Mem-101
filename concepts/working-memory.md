---
id: working-memory
title: "Working Memory"
kind: concept
stage: assemble
contrasts_with: [semantic-memory]
related: [context-window,token-budget]
status: published
---

# Working Memory

What is in front of the model **right now**: the current turn, the recent conversation, whatever was just retrieved. It is bounded, volatile, and dies when the session does.

## Why it matters in a memory layer

Working memory is the only memory an LLM has natively, and confusing it with a memory layer is the most common architectural mistake in this field. It answers "what are we talking about", never "what do I know about this person". Everything durable has to be written somewhere else on purpose.

## Connections

<!-- graph:begin -->
**Taught in:** [The Taxonomy That Actually Routes](../curriculum/beginner/memory-taxonomy/index.md)

**Used in:** [Context Is Not Memory](../curriculum/beginner/context-is-not-memory/index.md) · [Session Memory vs Long-Term Memory](../curriculum/beginner/session-vs-longterm/index.md)

**Do not confuse with:** [Semantic Memory](semantic-memory.md)
<!-- graph:end -->
