---
id: cross-writer-conflict
title: "Cross-Writer Conflict"
kind: concept
stage: evolve
contrasts_with: [memory-operations]
related: [competence, provenance, memory-topology]
status: published
---

# Cross-Writer Conflict

Two writers — an agent and the user, or two agents — claiming the same attribute, where one belief must be retired.

## Why it matters in a memory layer

Retrieval can return both sources and let the reader decide. A memory layer picks, the loser stops being retrievable, and the decision is invisible to whoever wrote the losing claim. A silent, permanent, unattributable choice is a different object from a ranked list.

The precedence rule that protects a user from hearsay is a **threshold, not a slope**. Above the line, it stops discriminating — so an agent at 0.9 and a user at 1.0 are the same to it, arbitration falls through to recency, and the agent wins by being newer. Scoring the *claim* rather than the claimant puts an out-of-domain assertion back below the line, where the rule works again.

Measure candidates on the **unconsolidated** store. Afterwards the losers are retired and excluded from candidate generation, so the count is zero — a clean number describing when you asked rather than what the corpus contains.

## Connections

<!-- graph:begin -->
**Taught in:** [Cross-Agent Write Conflicts](../curriculum/advanced/cross-agent-write-conflicts/index.md)

**Do not confuse with:** [Memory Operations](memory-operations.md)
<!-- graph:end -->
