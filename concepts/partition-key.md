---
id: partition-key
title: "Partition Key"
kind: concept
stage: store
contrasts_with: [growth-curve]
related: [retrieval-scoping, memory-topology, leak-assertion]
status: published
---

# Partition Key

What a store shards on — chosen, if you are lucky, before anyone asked about size.

## Why it matters in a memory layer

This course's store partitions on `user`, and it does so because that is the **correctness boundary**: ranking across tenants returns somebody else's facts, and nothing errors when it does.

That the same key also bounds the comparison groups consolidation works over is a fortunate coincidence rather than a design. The two requirements agreed here; had the cheapest partition for balance cut across users, safety would have had to win and the cost would have been paid elsewhere.

So the order matters. Pick the key that must never be violated, then measure whether it also bounds the curve — not the reverse.

## Connections

<!-- graph:begin -->
**Taught in:** [Scaling the Store](../curriculum/advanced/scaling-the-store/index.md)

**Do not confuse with:** [Growth Curve](growth-curve.md)
<!-- graph:end -->
