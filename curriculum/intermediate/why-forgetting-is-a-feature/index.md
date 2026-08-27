---
id: why-forgetting-is-a-feature
title: "Why Forgetting Is a Feature"
level: intermediate
stage: evolve
estimated_minutes: 30
concepts_taught: [relevance-vs-truth]
concepts_required: [token-budget, over-extraction, supersession]
lessons_required: [supersession-not-deletion]
capstone_piece: memlab.forget.audit
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Why Forgetting Is a Feature

> **In one line.** Three of the five memories the model receives are doing no work, and the cost of that is per-query and permanent — storage was never the reason to forget.

## Where this sits

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** intermediate · **~30 min**

**You need first:** [Supersede, Never Destroy](../supersession-not-deletion/index.md)

**Concepts assumed:** [Token Budget](../../../concepts/token-budget.md) · [Over-Extraction](../../../concepts/over-extraction.md) · [Supersession](../../../concepts/supersession.md)

**This unlocks:** [Salience Scoring](../salience-scoring/index.md)
<!-- graph:end -->

## The problem

I4 made the beliefs correct. Ask the exam question and look at what the model actually gets:

```
2 of 5 slots useful — 60% wasted

  wasted: Priya mostly does pipeline work
  wasted: Priya's weekly report process: pull pipeline metrics from ...
  wasted: Priya used to cycle to work before the move
```

Three of five slots carry claims the question does not need. **The employer is not among the five at all.**

The usual argument for forgetting is storage, and storage is the one resource here that is genuinely cheap — 37 memories is nothing. The costs that matter are per-*retrieval*: every memory is embedded once and then ranked on **every query forever**, competing for a token budget that does not grow with the store.

At this corpus's rate, 13 sessions produced 37 memories. A hundred and thirty sessions produces **370** — and the budget is still five slots.

## Why this isn't RAG

A retrieval index gets *better* as the corpus grows: more documents means more chance the right passage exists. Nothing is competing for a fixed slot count, because the corpus is not about one person and a query about Kubernetes never has to beat a document about payroll.

A memory store is about **one person**, so everything in it is plausibly relevant to everything they ask. Growth is not additional coverage; it is additional competition for the same five slots. That inverts the sign: in retrieval, more is better; in memory, more is worse unless it earns its place.

## Mechanism

Four reasons to forget, only one of which is about disk.

**Precision.** The scarce resource is context slots, and they are fixed. Every junk memory is a slot a useful one did not get.

**Latency and cost.** Ranking is linear in the store. So is re-embedding after an update, and so is every consolidation pass.

**Privacy.** Data you no longer hold cannot leak. The strongest form of a deletion guarantee is not having kept it.

**Coherence.** A store full of superseded, half-relevant material makes the model's job harder, not easier. `retrieval-is-not-enough` measured this directly: raising `k` monotonically increased the number of live contradictions in context.

### What forgetting is not

**Forgetting is not supersession.** They answer different questions, and the distinction is the whole of `relevance-vs-truth`:

| | trigger | what it means | mechanism |
|---|---|---|---|
| **supersession** | a newer claim contradicts it | the belief is **false** | `invalid_at`, I4 |
| **forgetting** | nothing has needed it for a long time | the belief is **still true** | salience and decay, this module |

Collapsing them produces both classic failures. Treat fading as falsification and you retire facts nobody contradicted. Treat falsification as fading and stale beliefs linger because they are recent.

**And forgetting is not deletion.** A faded memory is still true and the store holds the only copy, so eviction here is tier demotion — the same supersede-never-destroy discipline, applied to a different trigger.

## Design decisions

**Forget on a schedule, or under pressure?** Under pressure. A time-based sweep forgets things nobody needed to forget, and it makes the store's contents depend on how often a job ran — the same non-idempotency `semantic-drift` warned about.

**Cap the store or cap the retrievable tier?** The retrievable tier. The cost is per-query and per-slot, so bounding what retrieval *scans* is the thing that bites; bounding the log saves storage, which was never the problem.

**Let the user see what was forgotten?** Yes, and this is a genuine product requirement rather than a nicety. A system that quietly drops things it was told is worse than one that never remembered — the first breaks a promise it made.

## Lab

**You'll implement:** `audit_context` and `projected_growth`.

**Run:**
```
uv run python curriculum/intermediate/why-forgetting-is-a-feature/lab/lab.py
```

**Expected output:** **2 of 5** slots useful at both `@I4` and `@I5`, the three wasted rows named, and the growth projection: **37** memories from 13 sessions, **370** at 130.

**Stretch:** run the audit at `k=20` instead. The employer finally appears and the waste rises to over 80% — you bought the right answer by paying for fifteen wrong ones. Raising `k` does not improve the ratio; it is the ratio that has to change.

## What this adds to the capstone

`memlab.forget.audit` — `audit_context`, `projected_growth`, `tier_census`. Measurement only; the next three lessons act on it.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Answers degrade as history grows | Fixed slots, growing competition | Audit useful-slot ratio over account age | Salience and eviction |
| Forgetting retires true facts | Fading treated as falsification | Look for `invalid_at` set with no superseding claim | Separate the two triggers |
| Store contents depend on job frequency | Time-based sweeps | Run the sweep twice; diff | Forget under pressure, idempotently |
| Users lose things they explicitly asked you to keep | No explicit-marker signal in salience | Test a single unrepeated instruction | Weight explicit markers highest |
| Cost grows and nobody notices | Only storage is monitored | Track ranked-candidates per query | Cap the retrievable tier |

## Check yourself

??? question "37 memories is nothing. Why forget anything yet?"
    Because the mechanism has to exist before the pressure does, and the pressure arrives as a slow degradation rather than an incident. At 370 memories nothing breaks — answers just get slightly worse every month, which is the hardest kind of regression to notice or attribute.

??? question "In retrieval, a bigger corpus is better. Why is a bigger memory store worse?"
    Because a document corpus is about many subjects and a query only competes against the relevant slice. A memory store is about one person, so everything in it is plausibly relevant to everything they ask, and every addition competes for the same five slots.

??? question "Would deleting the three wasted memories fix this?"
    It would fix this question and break others. *"Priya's weekly report process"* is one of the most important things in the store — it is simply not what was asked. That is the trap the next lesson walks into deliberately: importance and relevance are different axes, and forgetting must not be driven by the wrong one.

## Connections

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** intermediate · **~30 min**

**You need first:** [Supersede, Never Destroy](../supersession-not-deletion/index.md)

**Concepts assumed:** [Token Budget](../../../concepts/token-budget.md) · [Over-Extraction](../../../concepts/over-extraction.md) · [Supersession](../../../concepts/supersession.md)

**This unlocks:** [Salience Scoring](../salience-scoring/index.md)
<!-- graph:end -->
