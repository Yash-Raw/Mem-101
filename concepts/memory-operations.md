---
id: memory-operations
title: "Memory Operations"
kind: concept
stage: evolve
contrasts_with: []
related: [belief-updating,supersession]
status: published
---

# Memory Operations

The vocabulary of write-path changes: ADD, UPDATE, MERGE, NOOP — and, separately from all of them, DELETE.

## Why it matters in a memory layer

The standard mistake is letting a model pick from this list directly. Asked what to do with two memories it will confidently answer UPDATE for a pair it misread, overwrite a correct belief, and leave no trace — the largest source of silent corruption in this kind of system. The model's contribution should be one thing: what the relationship *is*. The mapping from relationship to operation is policy, and belongs in a lookup table you can read, test, and diff.

## Connections

<!-- graph:begin -->
**Taught in:** [ADD, UPDATE, MERGE, NOOP](../curriculum/intermediate/memory-operations/index.md)

**Used in:** [Cross-Agent Write Conflicts](../curriculum/advanced/cross-agent-write-conflicts/index.md) · [LLM as Judge, and Its Failure Modes](../curriculum/advanced/llm-as-judge-for-memory/index.md) · [Deterministic Arbitration](../curriculum/intermediate/deterministic-freshness/index.md) · [Supersede, Never Destroy](../curriculum/intermediate/supersession-not-deletion/index.md)
<!-- graph:end -->
