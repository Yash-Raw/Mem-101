---
id: caching-batching-routing
title: "Caching, Batching, Routing"
level: advanced
stage: govern
estimated_minutes: 45
concepts_taught: [cache-key, model-routing]
concepts_required: [cost-profile, latency-budget, vector-index]
lessons_required: [latency-budget]
capstone_piece: memlab.cost.tactics
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Caching, Batching, Routing

> **In one line.** The cache everyone reaches for saves nothing, and the one that works was shipped two levels ago for a different reason.

## Where this sits

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [The Latency Budget](../latency-budget/index.md)

**Concepts assumed:** [Cost Profile](../../../concepts/cost-profile.md) · [Latency Budget](../../../concepts/latency-budget.md) · [Vector Index](../../../concepts/vector-index.md)

**This unlocks:** [Scaling the Store](../scaling-the-store/index.md)
<!-- graph:end -->

## The problem

Three tactics, applied against the profile `cost-model` measured — 48 model calls and 38 embeddings on the write path, zero calls on the read:

```
tactic                                applies  saving
cache completions                       False  nothing
cache embeddings                         True  18 embeds per read
batch extraction                         True  48 calls -> fewer, same work
route extraction to a small model        True  50% of the per-turn cost
route conflict detection                 True  the other 50%
route arbitration                       False  nothing

apply: 4 of 6
already shipped: ['cache embeddings']
```

**Caching completions is the first thing anyone proposes and it buys nothing.** The cache key is the turn's text, every turn's text is different, and the key never repeats. That is not a tuning problem — it is what a conversation is.

## Why this isn't RAG

A retrieval stack caches at the read path, where the same query recurs across users and the same passages come back. Popular queries are genuinely popular, so a completion cache has real hit rates and is the standard first optimisation.

A memory layer's expensive path is the write path, and **every write is unique by construction** — it is one person saying something they have not said before. There is no popularity distribution to exploit. The cacheable thing here is not the call, it is the *embedding of a stored memory*, which recurs because the memory persists.

## Mechanism

**Cache on something stable, and the id already is one.** `VectorIndex` is keyed on the content-addressed `Memory.id`, so a warm read costs **2** embeddings and a cold one costs **20**. That was built in I7 to stop re-embedding the corpus per query; the cost saving is the same mechanism read from the other side, and nobody designed it as a cost optimisation.

**Batching changes the count, not the work — and only on a backfill.** Live turns arrive one at a time, so extraction cannot be batched without waiting, which is a latency decision rather than a cost one. A backfill or a migration can batch, and that is where the tactic belongs.

**Routing has two targets, not one.** `latency-budget` measured the per-turn cost as an even split — extraction, synchronous, and `conflict.classify`, entirely deferred — and **both are bounded tasks**: a schema on one side, four labels on the other. That is the shape small models fit.

The stage with nothing to route is *arbitration*, which `deterministic-freshness` made rules. An earlier version of this lesson confused arbitration with conflict **detection** and reported one target covering 81%; detection is a model call, and it is the other half.

**Two of six tactics do not apply, and that is the deliverable.** A cost review that lists six tactics and recommends all six has not looked at a profile.

## Design decisions

**Why is "cache completions" listed if it does not apply?** Because it is the default proposal, and a lesson that only lists the tactics that work leaves the reader to rediscover why the obvious one fails. The reason — every turn's text differs — is one sentence and it generalises to any conversational write path.

**Why not implement routing?** Because this course runs against a deterministic fake with no notion of model size, so an implementation would be a config flag with nothing behind it. What is measurable is *where* routing would apply and how much it covers, and that is both halves of the write path, with a stated reason for each.

**Why does batching's saving say "same work"?** Because it is fewer calls over the same tokens, and which of those a bill is denominated in varies. Reporting it as a call reduction without that qualifier is how a batching change gets adopted for a saving that does not appear.

## Lab

**You'll implement:** `assess`, `headroom`, and `already_shipped`.

**Run:**
```
uv run python curriculum/advanced/caching-batching-routing/lab/lab.py
```

**Expected output:** the six tactics with two marked inapplicable, **4 of 6** applying, and `cache embeddings` reported as already shipped.

**Stretch:** compute the completion cache's hit rate over the corpus by keying on turn text. It is **zero** — 24 turns, 24 distinct keys — and the same computation over the *memory* ids finds the reuse the vector index is already exploiting. **The cache that works is keyed on what persists, not on what arrives.**

## What this adds to the capstone

`memlab.cost.tactics` — `Tactic`, `assess`, `headroom`, `already_shipped`. A review over `cost-model`'s and `latency-budget`'s numbers; it implements no tactic, and says which ones there would be nothing behind.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Completion cache with no hits | Key is the incoming turn | Count distinct keys over the corpus | Key on what persists |
| Batching adopted, bill unchanged | Fewer calls, same tokens | Ask what the bill is denominated in | State the unit |
| Routing applied to rules | Confused arbitration with conflict detection | Grep each stage for a client call | Check before routing |
| Every tactic recommended | No profile consulted | Ask which ones do not apply | Report the inapplicable |
| Cost win claimed for old work | Mechanism built for another reason | Check when it shipped | Attribute it honestly |

## Check yourself

??? question "Why does a completion cache work in a retrieval stack and not here?"
    Because retrieval reads a shared corpus and queries follow a popularity distribution — the same question really is asked repeatedly. A memory layer's expensive path is writes, and a write is one person saying something new. There is no distribution to exploit, and no key design fixes that.

??? question "The embedding cache saves 18 embeddings per read. Was that a cost decision?"
    No — I7 built it to stop re-embedding the whole corpus on every query, which was a scaling problem measured as embed-calls-per-query. The cost saving is the identical mechanism viewed from a different column, and claiming it as a cost optimisation would misattribute work done two levels earlier for a different reason.

??? question "Routing covers the whole write path. Why not just do it?"
    Because "route to a small model" is a claim that a smaller model performs the task adequately, and that needs an evaluation this course has the machinery for and has not run. What the lesson establishes is that both targets are well chosen — bounded output on each side — which is the part knowable from the profile alone. It also establishes which stage is *not* a target, and that one was got wrong first: arbitration is rules, conflict detection is a model call, and the names are one word apart.

## Connections

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [The Latency Budget](../latency-budget/index.md)

**Concepts assumed:** [Cost Profile](../../../concepts/cost-profile.md) · [Latency Budget](../../../concepts/latency-budget.md) · [Vector Index](../../../concepts/vector-index.md)

**This unlocks:** [Scaling the Store](../scaling-the-store/index.md)
<!-- graph:end -->
