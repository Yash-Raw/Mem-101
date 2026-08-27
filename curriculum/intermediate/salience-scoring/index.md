---
id: salience-scoring
title: "Salience Scoring"
level: intermediate
stage: evolve
estimated_minutes: 45
concepts_taught: [salience, reinforcement]
concepts_required: [relevance-vs-truth, durability-gate, corroboration]
lessons_required: [why-forgetting-is-a-feature]
capstone_piece: memlab.forget.salience
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Salience Scoring

> **In one line.** Salience is importance and ranking wants relevance — and adding one to the other moves the correct answer from rank 20 to rank 22.

## Where this sits

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** intermediate · **~45 min**

**You need first:** [Why Forgetting Is a Feature](../why-forgetting-is-a-feature/index.md)

**Concepts assumed:** [Relevance vs Truth](../../../concepts/relevance-vs-truth.md) · [The Durability Gate](../../../concepts/durability-gate.md) · [Corroboration](../../../concepts/corroboration.md)

**This unlocks:** [Decay and Memory Tiers](../decay-and-tiers/index.md)
<!-- graph:end -->

## The problem

Every memory in the store sits at salience **0.5** with `access_count` **0**. The fields were designed in Beginner and nothing has ever populated them, so the system cannot distinguish a fact Priya insisted on from an afternoon's debugging.

Score them, and the obvious next move is to feed the number into the ranker. Better memories should rank higher. Try it:

| salience weight | employer rank | top result |
|--:|--:|---|
| 0.0 | 20 | *Priya does not eat meat* |
| 0.2 | **21** | *Priya's weekly report process…* |
| 0.5 | **22** | *Priya's weekly report process…* |

**It gets worse.** The correct answer sinks, and the memory salience promotes hardest — the weekly report procedure, at **0.95** — takes first place for a question about employment and diet.

Nothing is miscalibrated. That procedure genuinely is one of the most important things Priya ever said; she taught it deliberately and said the order mattered. **It is simply not what was asked.**

## Why this isn't RAG

Retrieval has one axis, and document-level priors — PageRank, freshness, authority — genuinely do improve it, because they correlate with which documents are *good*.

Memory has two axes that come apart hard. **Importance** is a property of the memory and barely moves. **Relevance** is a property of the question and is different every time. A taught procedure is permanently important and almost never relevant. Blending them produces a ranker that surfaces what matters most in general rather than what was asked — which reads as a system that will not listen.

## Mechanism

Four signals, all read off fields that already exist. Rules, not a model: a salience score that varies between runs cannot be debugged, and *"why did you forget that?"* deserves an answer.

| signal | weight | why |
|---|--:|---|
| **explicit** — the user said to remember it | +0.30 | the clearest evidence available, and nearly free |
| **corroboration** — per source in `derived_from` | +0.10 | independent assertion is evidence |
| **use** — per recall that reached the context | +0.05 | it keeps being needed |
| **activity** — a finished task | −0.25 | true once, over now |
| **hearsay** — `authority < 0.5` | −0.20 | relayed and unconfirmed |
| **procedure** — corrective bonus | +0.15 | see below |

The procedure bonus is a **correction for a known blind spot**, not a preference for the type. Procedures are taught once, deliberately, and almost never restated — so every reinforcement signal under-serves them. Naming that as a correction rather than folding it into the weights keeps it arguable.

Across the live store this yields six distinct values, from **0.5** to **0.95**.

**Reinforcement is the strongest signal and cannot be the only one.** `record_use` increments `access_count` when a memory is recalled *and assembled* — not merely scanned. It is the only signal that requires the system to have been running, which is exactly why a store ranked purely by past use never surfaces the fact stated once and never asked about until the day it matters.

### What salience is for

Not ranking. **Forgetting.** The next lesson uses it to decide what fades and what stays retrievable, which is a question about the memory rather than about the query — and that is the question salience actually answers.

## Design decisions

**Rules or a learned score?** Rules, and this is not a placeholder. A learned salience model would need labels nobody has, would vary between runs, and could not explain a demotion to a user who asks. Explicit markers and claim shape are cheap, auditable, and catch most of it.

**Store salience, or compute it per query?** Store it. It is a property of the memory, it changes slowly, and computing it per query would put a scan of `derived_from` on the read path for a number that barely moves.

**Should salience feed the ranker at all?** Not on its own, and the table above is why. It earns a place in [hybrid ranking](../hybrid-ranking/index.md) only *alongside* relevance and type-awareness, as one term among several — never as a multiplier on a relevance score.

## Lab

**You'll implement:** `score`, `apply`, and `record_use` — then the experiment that rejects the obvious use of them.

**Run:**
```
uv run python curriculum/intermediate/salience-scoring/lab/lab.py
```

**Expected output:** six distinct salience values across the live store, the weekly report procedure highest at **0.95**, and the ranking sweep above: employer at rank 20 → 21 → 22 as salience weight rises.

**Stretch:** call `record_use` on the four memories the exam actually needs, re-score, and re-run the sweep. They climb — reinforcement works — and the procedure is still first, because it started 0.45 ahead. A signal that needs a hundred uses to overcome a prior is not the mechanism fixing this.

## What this adds to the capstone

`memlab.forget.salience` — `score`, `apply`, `record_use`, and the weight table. It populates `Memory.salience` and `Memory.access_count`, which have defaulted since Beginner.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| The system answers what matters, not what was asked | Salience blended into relevance | Sweep the salience weight; watch the correct answer's rank | Keep the axes separate |
| Rarely-mentioned critical facts fade | Reinforcement weighted too heavily | Test a fact stated once and never revisited | Weight explicit markers above use |
| Taught procedures decay away | Every reinforcement signal under-serves them | Check salience by type | An explicit corrective bonus |
| Salience differs between runs | A model scoring it | Score the same store twice; diff | Rules |
| "Why did you forget that?" unanswerable | Score computed without recording its terms | Try to explain one demotion | Deterministic, per-signal weights |

## Check yourself

??? question "Adding salience to the ranker makes results worse. Was scoring it a mistake?"
    No — the score is needed, the *application* was wrong. The next lesson uses it to decide what fades out of the retrievable tier, which is a question about the memory. Ranking is a question about the query. Same number, and only one of the two questions it can answer.

??? question "The weekly report procedure scores 0.95 and is pure noise here. Is the weighting wrong?"
    The weighting is right and the use is wrong. Priya taught that procedure deliberately and said its order mattered; by any measure of importance it belongs near the top of the store. It is irrelevant to a question about diet, and no amount of importance makes it relevant.

??? question "Why is reinforcement worth only 0.05 when it is the strongest signal?"
    Because it is the only one that requires the system to have already been running, so early on it is zero for everything and a heavy weight would just amplify whatever happened to surface first. It is strong *evidence* and a poor *prior* — and its low weight is why the stretch experiment cannot rescue the ranking.

## Connections

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** intermediate · **~45 min**

**You need first:** [Why Forgetting Is a Feature](../why-forgetting-is-a-feature/index.md)

**Concepts assumed:** [Relevance vs Truth](../../../concepts/relevance-vs-truth.md) · [The Durability Gate](../../../concepts/durability-gate.md) · [Corroboration](../../../concepts/corroboration.md)

**This unlocks:** [Decay and Memory Tiers](../decay-and-tiers/index.md)
<!-- graph:end -->
