---
id: cost-model
title: "The Write Path Dominates"
level: advanced
stage: govern
estimated_minutes: 45
concepts_taught: [cost-profile, write-path-dominance]
concepts_required: [extraction-pipeline, vector-index, element-cost]
lessons_required: [reading-benchmark-claims]
capstone_piece: memlab.cost.profile
lab: lab/lab.py
lab_runtime: fake
status: published
---

# The Write Path Dominates

> **In one line.** The read path makes zero model calls — every one in the system happens while nobody is waiting.

## Where this sits

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [Reading Benchmark Claims Critically](../reading-benchmark-claims/index.md)

**Concepts assumed:** [The Extraction Pipeline](../../../concepts/extraction-pipeline.md) · [Vector Index](../../../concepts/vector-index.md) · [Element Cost](../../../concepts/element-cost.md)

**This unlocks:** [The Latency Budget](../latency-budget/index.md)
<!-- graph:end -->

## The problem

This course opened with a claim: RAG is a read path over a corpus someone else wrote, and a memory layer is dominated by the write path. Seventy-four lessons later it is measurable rather than rhetorical.

```
write path (full ingest, 24 turns)   llm  48   embed  38
read path  (one question)            llm   0   embed   2

ratio                                llm no model calls at all   embed 19x
per turn                             llm 2.0   embed 1.6
```

**Zero.** Not "cheap" — none. The read path is scope filtering, slot matching, cached vectors and arithmetic.

## Why this isn't RAG

A retrieval stack pays at read time: embed the query, search, rerank, and often a model call to compress or synthesise. Indexing is a one-off amortised across every future query, which is why "index once, query forever" is a sound way to think about the bill.

Invert it. Here indexing is *per turn, forever* — every message costs two model calls whether or not anyone ever asks a question about it — and the query is free. **The economics run the opposite way, and so does the optimisation advice**: caching queries buys nothing, and a cheaper extractor is the whole game.

## Mechanism

**Count by patching, and then find out that patching is not enough.** `counting()` replaces `fake.embed_text` — and four modules did `from ..llm.fake import embed_text`, which **copies the reference into their own namespace**, so the patch never reaches them. The first version of this profiler patched one of the four.

The numbers here happen to be identical either way, which is worse than if they had moved: a silently low count that agrees with the correct one teaches you to trust the method. So `_IMPORTERS` is a maintained list, and a test derives the real set from the source and asserts they match.

**2.0 model calls per turn, and it scales with the conversation.** Not with the store — extraction reads one turn. That is the number to quote when someone asks what a year of use costs: it is linear in messages, and independent of how much has been remembered.

**The embedding count is the one that used to scale badly.** `vector-stores-for-mutable-data` measured 2N embed calls per *query* before caching; the read path now costs **2** — one for the query, one the index had not reached. Skip the indexing pass and the same read costs **20**, which is what the 19× ratio is actually buying.

**Zero read-path model calls is a design outcome, not an accident.** `deterministic-freshness` refused to let a model arbitrate, `hybrid-ranking` scores with arithmetic, and `assemble` packs by counting tokens. Each was argued for on correctness grounds — reproducibility, explainability, determinism — and the cost profile is what those arguments bought without anyone optimising for it.

## Design decisions

**Why count calls rather than seconds?** Because seconds are a property of the machine and the provider, and this corpus runs against a deterministic fake. Calls are the invariant: they are what a bill is denominated in, and they do not change when the hardware does. `latency-budget` splits the same calls by deadline rather than introducing a clock — nothing in this course measures wall-clock, because against a deterministic fake it would measure the laptop.

**Why is the read path measured on one question?** Because that is the unit a user experiences. A per-session or per-day figure hides the thing that matters — what one answer costs — and the answer here is two embeddings and no model call, which is small enough to state without qualification.

**Why not amortise the write path across questions asked?** Because most turns are never asked about. Amortising assumes a query rate, and the honest framing is that extraction is paid unconditionally: the system remembers the whole conversation, and the questions are a separate, cheaper stream.

## Lab

**You'll implement:** `counting` and `ratio`.

**Run:**
```
uv run python curriculum/advanced/cost-model/lab/lab.py
```

**Expected output:** the write path at **48** model calls and **38** embeddings, the read path at **0** and **2**, the ratio reporting *no model calls at all*, and **2.0** / **1.6** per turn.

**Stretch:** run the read without calling `index()` first. It costs **20** embeddings instead of 2, embedding on demand exactly as the 2N-per-query behaviour I7 removed. **The read path is cheap only because the write path paid for it** — and the model cost is zero in both configurations, which is the number the headline rests on.

## What this adds to the capstone

`memlab.cost.profile` — `Cost`, `counting`, `ratio`. Patches the fake client for the duration of a block, so new call sites are counted without being registered.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Cost optimised on the read path | RAG intuitions applied | Count calls on each path | Measure before optimising |
| A new model call goes uncounted | `from x import y` copied the reference | Derive the importer set from source | Patch every importer |
| Bill scales with the store | Embeddings computed per query | Count embeds as the store grows | Cache by content id |
| Cost quoted per session | Hides the per-answer figure | Ask what one answer costs | Report the user's unit |
| Cheap read path assumed free | Write path paid for it | Skip indexing and re-measure | Attribute the saving |

## Check yourself

??? question "Zero model calls on the read path. Was that optimised for?"
    No, and that is the interesting part. Arbitration refuses a model for explainability, ranking uses arithmetic for determinism, and packing counts tokens because a budget is arithmetic. Every one of those was argued on correctness grounds two levels earlier, and the cost profile is the side effect. Optimising for it directly would have meant the same decisions with worse reasons.

??? question "Why is per-turn cost the number to quote, rather than total?"
    Because it is the one that predicts a bill. Two model calls per message is linear in conversation length and independent of how much has been remembered, so a year of use is arithmetic. A total over one corpus answers a question nobody asks.

??? question "The read path costs two embeddings. Why not one?"
    One is the query, which cannot be cached because it is new. The second is a memory the vector cache did not hold — so the steady-state cost is one, and the second is the tail of a warming index. That distinction only exists because I7 made vectors content-addressed and reusable; before it, the figure grew with the store on every query.

## Connections

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [Reading Benchmark Claims Critically](../reading-benchmark-claims/index.md)

**Concepts assumed:** [The Extraction Pipeline](../../../concepts/extraction-pipeline.md) · [Vector Index](../../../concepts/vector-index.md) · [Element Cost](../../../concepts/element-cost.md)

**This unlocks:** [The Latency Budget](../latency-budget/index.md)
<!-- graph:end -->
