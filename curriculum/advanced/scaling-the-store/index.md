---
id: scaling-the-store
title: "Scaling the Store"
level: advanced
stage: store
estimated_minutes: 50
concepts_taught: [growth-curve, partition-key]
concepts_required: [cost-profile, slot, retrieval-scoping]
lessons_required: [caching-batching-routing]
capstone_piece: memlab.cost.scale
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Scaling the Store

> **In one line.** Eight times the store is eight times the retrieval pool and a hundred and four times the conflict candidates.

## Where this sits

<!-- graph:begin -->
**Stage:** `store` · **Level:** advanced · **~50 min**

**You need first:** [Caching, Batching, Routing](../caching-batching-routing/index.md)

**Concepts assumed:** [Cost Profile](../../../concepts/cost-profile.md) · [Slot](../../../concepts/slot.md) · [Retrieval Scoping](../../../concepts/retrieval-scoping.md)
<!-- graph:end -->

## The problem

`graph-stores` set the rule: measure the shape before adopting the architecture. So replicate the corpus rather than asserting that a store needs partitioning, and watch which costs move.

```
  x  memories  eligible   pairs  pairs/mem
  1        37        18       9        0.2
  2        74        36      49        0.7
  4       148        72     222        1.5
  8       296       144     940        3.2
```

**Retrieval grows linearly and consolidation does not.** Eight times the store gives eight times the eligible pool — and **104 times** the candidate pairs. The stage that breaks first is not the one users touch.

## Why this isn't RAG

Retrieval scales by sharding the index: more documents, more shards, and a query fans out and merges. The unit of work is a query against a partition, and partitions are chosen for balance.

A memory layer's expensive stage compares memories **with each other**, so its cost is a function of how many live in the same comparison group. That is not fixed by adding shards — it is fixed by making the groups smaller, which is a modelling decision rather than an infrastructure one.

## Mechanism

**Replication needs distinct ids or it measures nothing.** `Memory.id` is content-addressed, so a naive copy deduplicates itself back into the original — the store working exactly as designed and useless here. Varying the source id makes the copies genuinely distinct records.

**Candidate pairs are the curve to watch.** I3 blocked candidate generation by `SLOT` precisely to avoid comparing everything with everything, and **within a slot it is still all-pairs**. Replication multiplies the members of each slot, so the pairs grow with the square of the group — 0.2 pairs per memory at 1×, 3.2 at 8×.

The blocking is doing real work; it is bounding the *number of groups*, not the size of one. A store with a thousand beliefs about diet has the same problem the slot table was introduced to solve, one level down.

**The eligible pool grows linearly, and the tier cap does not save it.** `forget.budget` caps LONG_TERM at 20 per store, and eight replicated stores are eight caps. Under real growth the cap binds; under replication it does not, and that difference is worth naming — **this measurement models many users, not one user talking for eight times as long.**

**The partition key was never a scaling decision.** `scopes.partition` shards on `user`, and it does so because that is where the correctness boundary is:

```
user -- fixed by scopes.partition as a correctness boundary, before size was
a consideration
```

Which is the fortunate case. The key a store must shard on for safety is also the key that bounds the comparison groups, so the two requirements agree — and if they had disagreed, safety would have had to win.

## Design decisions

**Why replicate rather than generate a synthetic corpus?** Because a generated corpus changes the content distribution, and every number in this course is measured against one conversation. Replication holds the distribution fixed and varies only the size, so a change in the curve is attributable to size alone. It also models the wrong thing in a known way — many users rather than a long conversation — which is a stated limitation rather than a hidden one.

**Why measure pairs rather than time?** Same reason as the two previous lessons: pairs are the invariant. A pair is a comparison the system must perform regardless of hardware, and pair counts transfer between deployments in a way milliseconds do not.

**Why does this lesson build no partitioning?** Because the store already partitions on the right key, for a better reason. What was missing was the measurement showing which cost actually forced the question — and the answer is consolidation, not retrieval, which is not where anyone looks first.

## Lab

**You'll implement:** `replicate`, `measure`, and `partition_key`.

**Run:**
```
uv run python curriculum/advanced/scaling-the-store/lab/lab.py
```

**Expected output:** the four-row growth table — **37/18/9** at 1× and **296/144/940** at 8× — with pairs per memory going **0.2 → 3.2**, and the partition key reported as `user`.

**Stretch:** replicate without varying the source id. Every count stays at 1×'s values, because content-addressed ids collapse the copies — the store deduplicating a corpus that was never really there. **A scaling harness that measures nothing looks exactly like a system that scales perfectly.**

## What this adds to the capstone

`memlab.cost.scale` — `Growth`, `replicate`, `measure`, `partition_key`. **Module A8 ends here**: the write path priced, the latency split, the tactics reviewed, and the growth curve measured rather than assumed.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Scaling work aimed at retrieval | Assumed the read path degrades first | Measure both curves | Replicate and compare |
| Harness shows perfect scaling | Content-addressed ids collapsed the copies | Check the store size actually grew | Vary the source id |
| Blocking assumed to bound cost | It bounds group count, not group size | Count pairs per memory | Measure within a slot |
| Partition key chosen for balance | Correctness boundary ignored | Ask what must never be mixed | Shard on the boundary |
| Cap assumed to hold at scale | Replication multiplies caps | Ask what the measurement models | Name the limitation |

## Check yourself

??? question "Slot blocking exists to avoid comparing everything with everything. Why do the pairs still explode?"
    Because it bounds the number of groups, not the size of one. Every memory claiming `diet` is compared with every other, so a slot with a thousand members generates half a million pairs — the problem the slot table solved, one level down. The fix is smaller groups, which is a modelling change rather than an infrastructure one.

??? question "The eligible pool grows linearly. Doesn't the I5 tier cap bound it?"
    It does, per store, at 20 long-term memories. Replication produces eight stores and therefore eight caps, so the cap does not bind here — which makes this measurement a model of many users rather than of one user talking eight times as long. Both are real situations and only one of them is being measured.

??? question "Why does it matter that the partition key was chosen for correctness?"
    Because it means the two requirements agreed, and they need not have. Sharding on `user` bounds the comparison groups and enforces the tenant boundary at the same time — but if the cheapest partition for balance had cut across users, the safe key would have had to win, and the cost would have been paid somewhere else.

## Connections

<!-- graph:begin -->
**Stage:** `store` · **Level:** advanced · **~50 min**

**You need first:** [Caching, Batching, Routing](../caching-batching-routing/index.md)

**Concepts assumed:** [Cost Profile](../../../concepts/cost-profile.md) · [Slot](../../../concepts/slot.md) · [Retrieval Scoping](../../../concepts/retrieval-scoping.md)
<!-- graph:end -->
