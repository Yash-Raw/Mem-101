---
id: sleep-time-compute
title: "Sleep-Time Compute"
level: advanced
stage: evolve
estimated_minutes: 50
concepts_taught: [sleep-time-compute, consistency-window]
concepts_required: [deduplication, slot, supersession]
lessons_required: [temporal-knowledge-graphs]
capstone_piece: memlab.sleep.schedule
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Sleep-Time Compute

> **In one line.** Deferring consolidation costs nothing in accuracy and eleven turns of correctness — and the gate that buys those turns back cheaply is not the one you would reach for.

## Where this sits

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** advanced · **~50 min**

**You need first:** [Temporal Knowledge Graphs](../temporal-knowledge-graphs/index.md)

**Concepts assumed:** [Deduplication](../../../concepts/deduplication.md) · [Slot](../../../concepts/slot.md) · [Supersession](../../../concepts/supersession.md)
<!-- graph:end -->

## The problem

`ingest()` consolidates **once**, after the last turn. That is not a design decision, it is an artifact of the corpus arriving all at once. Replay it a turn at a time, the way a live system receives it:

```
                          runs   embed   cosine   final live
defer everything             1      38      282           30
consolidate every turn      25     503     1630           30
```

**13× the embeddings, 5.8× the comparisons, and the identical store.** Consolidation is order-independent here — which is the finding that makes deferral safe at all, and it was worth measuring rather than assuming.

So the compute is not the cost. This is:

```
turns on which the deferred store believes a fact the consolidated
one has retired:   11 of 24, from turn 14 (session 8) to turn 24
```

**46% of the conversation still believing she works at Northwind** — including session 9, the turn where she corrects the assistant about exactly that. Ask a question inside that window and the batch job's efficiency is irrelevant.

## Why this isn't RAG

Indexing is a background job in every retrieval system, and the staleness window is understood and usually fine: a document indexed an hour late is a document you cannot cite for an hour. The corpus does not contradict itself in the meantime, because the old document is still correct.

A memory layer's deferred work is **arbitration**, not indexing. The window is not "a fact is missing"; it is "the system actively believes something the user has already corrected." Those fail differently — one omits, the other argues — and only the second one makes the user repeat themselves.

## Mechanism

**Gate consolidation on the turn, not the clock.** The question is which turns cannot wait.

**The obvious gate is memory type**, and it barely works. Standing beliefs get contradicted; events and taught procedures do not. But **24 of the 35 memories are semantic and 18 of 24 turns write one**, so the filter fires nearly always:

| gate | runs | embed | cosine | wrong turns |
|---|--:|--:|--:|--:|
| never — defer everything | 1 | 38 | 282 | **11** |
| by memory type | 19 | 365 | 1199 | 0 |
| **by contested slot** | **11** | **281** | **1011** | **0** |
| always — every turn | 25 | 503 | 1630 | 0 |

**The gate that works is the one the write path already computes.** A window opens only when a turn claims a `SLOT` something live already claims — the same table I4 uses to generate conflict candidates, asked one stage earlier. Nothing new is computed; the scheduler reads a decision the system was going to make anyway.

**44% of the runs, 56% of the embeddings, and zero wrong turns.** Against the type gate it is not a marginal improvement — it is 8 fewer consolidations for the same correctness, because it fires on *contradiction* rather than on a proxy for it.

**Pass the store as it stood before the turn.** Passing the post-write store makes a turn contested by its own writes: **11 runs becomes 18**, with identical output. It does not become `always`, which is the trap — a gate that failed completely would be visible in a cost graph, and one that half-fails reads as a gate that works.

The employer slot is claimed in session 1 and then contested in **sessions 8 and 9** — the announcement and the correction. Those are exactly the two turns the deferred store gets wrong, and the gate finds them without being told what an employer is.

## Design decisions

**Why not just always consolidate inline?** Because on this corpus it costs 503 embeddings against 281 for the same answer, and this corpus is 37 memories. The pass is over the whole store, so the cost grows with what you have remembered while the benefit stays fixed at "the few turns that contest something."

**Why is `never` still worth shipping?** Because it is correct for a store nobody is querying between writes — a nightly import, a backfill, a migration. The window only costs you if someone is asking.

**Why does the SLOT table keep appearing?** Because it is the only place the system names *what a memory claims*, and that is the question conflict detection, ranking and now scheduling all need. `slot-value` measured that removing a slot silently reverts the exam; this adds a third caller with the same property.

**What this does not fix.** The store is still consolidated by a read-modify-write with no guard — `store.replace(consolidate(store.all()))`. Running it more often makes the race more likely, not less. That is the next lesson.

## Lab

**You'll implement:** `Schedule.needs_inline`.

**Run:**
```
uv run python curriculum/advanced/sleep-time-compute/lab/lab.py
```

**Expected output:** the four gates measured — **1 / 19 / 11 / 25** runs, **38 / 365 / 281 / 503** embeddings, and **11 / 0 / 0 / 0** wrong turns — all four ending at **30** live memories.

**Stretch:** pass the store *after* the turn's writes instead of before. Runs go from **11 to 18**, the output is unchanged, and nothing looks broken. It does not degrade all the way to `always` — which is worse than if it had. 25 would show up in a cost graph as a gate that stopped working; **18 looks like a gate that works and is simply less effective than the measurement promised.**

## What this adds to the capstone

`memlab.sleep.schedule` — `Gate`, `Schedule`, `needs_inline`, and the `never` / `by_type` / `always` / `default` constructors. `Pipeline.sleep` is switched on at A2; `None` keeps the batch behaviour every earlier snapshot was measured against.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| System argues with a correction | Consolidation deferred past the contested turn | Replay turn by turn, diff against eager | Gate on contested slots |
| Scheduler saves nothing | Gated on type; the type dominates | Count turns the gate fires on | Gate on what is contested |
| Gate always fires | Post-write store passed as "stored" | Compare run count to `always` | Pass the pre-turn store |
| Cost grows with the store | Consolidation is a full pass | Measure embeddings per turn as it grows | Fewer passes, not cheaper ones |
| Deferral changes the answer | Consolidation not order-independent | Diff deferred vs eager final stores | Measure before deferring |

## Check yourself

??? question "Deferring is 13× cheaper and reaches the same store. What is the argument against it?"
    Eleven turns. The final state is identical, and the store is queried *during* the run, not after it — so "converges to the same answer" describes a property nobody experiences. The user experiences the window, and in this corpus the window contains the turn where they correct the assistant about their job.

??? question "Why does gating on memory type barely help?"
    Because the type that matters is the type that dominates. Semantic memories are the ones that get contradicted, and they are 24 of 35 memories spread across 18 of 24 turns, so a filter for "did this turn write a standing belief?" is nearly the constant `True`. The gate has to distinguish turns, and type does not.

??? question "The contested-slot gate needs no new computation. Why is that the point rather than an aside?"
    Because a scheduler that needs its own analysis pass has to be scheduled too. Reading `slot_of` on the turn's output is work the write path performs a moment later anyway, so the decision is free — and free is what lets it run on the critical path, which is the only place it can run.

## Connections

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** advanced · **~50 min**

**You need first:** [Temporal Knowledge Graphs](../temporal-knowledge-graphs/index.md)

**Concepts assumed:** [Deduplication](../../../concepts/deduplication.md) · [Slot](../../../concepts/slot.md) · [Supersession](../../../concepts/supersession.md)
<!-- graph:end -->
