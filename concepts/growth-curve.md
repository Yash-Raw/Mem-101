---
id: growth-curve
title: "Growth Curve"
kind: concept
stage: store
contrasts_with: [partition-key]
related: [slot, cost-profile, deduplication]
status: published
---

# Growth Curve

Which costs move as the store grows — measured by replicating a real corpus rather than reasoned about.

## Why it matters in a memory layer

Retrieval scales by sharding: more documents, more shards, a query fans out and merges. A memory layer's expensive stage compares memories **with each other**, so its cost is a function of how many share a comparison group, and adding shards does not shrink a group.

Measured here, eight times the store is **eight times the eligible pool and 104 times the candidate pairs**. The stage that breaks first is not the one users touch.

Slot blocking is doing real work and it bounds the *number* of groups, not the size of one: within a slot the comparison is still all-pairs, so pairs per memory climb from 0.2 to 3.2. A store with a thousand beliefs about one attribute has the problem the slot table was introduced to solve, one level down.

Replicate rather than generate, so only size varies and a change in the curve is attributable to size — and say what the harness models. Replication is many users, not one user talking for eight times as long, which matters because per-store caps multiply instead of binding.

## Connections

<!-- graph:begin -->
**Taught in:** [Scaling the Store](../curriculum/advanced/scaling-the-store/index.md)

**Do not confuse with:** [Partition Key](partition-key.md)
<!-- graph:end -->
