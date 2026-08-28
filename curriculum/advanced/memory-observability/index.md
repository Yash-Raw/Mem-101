---
id: memory-observability
title: "Memory Observability"
level: advanced
stage: govern
estimated_minutes: 45
concepts_taught: [memory-diff, memory-observability]
concepts_required: [provenance, bi-temporal-modeling, derivation-graph]
lessons_required: [failure-field-guide]
capstone_piece: memlab.production.observe
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Memory Observability

> **In one line.** Six kinds of *"why do you think that?"* are answerable with no logging at all, and the three that are not all need something written down at read time.

## Where this sits

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [The Failure Field Guide](../failure-field-guide/index.md)

**Concepts assumed:** [Provenance](../../../concepts/provenance.md) · [Bi-Temporal Modeling](../../../concepts/bi-temporal-modeling.md) · [Derivation Graph](../../../concepts/derivation-graph.md)

**This unlocks:** [Invariants and Drift Detection](../invariants-and-drift-detection/index.md)
<!-- graph:end -->

## The problem

Two lessons hit this gap without naming it. `implicit-signals` wanted a retrieval log to attribute a correction and had to reconstruct from the assistant's wording. `deletion-that-actually-deletes` needed to know which structures held a value and had to be told by hand.

But most of the answer is already in the record:

```
-- data engineer at Northwind
   content   Priya is a data engineer at Northwind Labs
   source    s1:2025-03-04T09:12:00Z
   speaker   user (authority 1.0)
   true      2025-03-04 .. 2025-12-08
   believed  2025-03-04 .. 2025-12-08
   retired by Priya is a staff engineer
```

**No log was consulted.** The turn, the speaker, both validity spans and the supersession chain are fields that `the-memory-record`, `two-clocks` and `supersession-not-deletion` put there for other reasons.

## Why this isn't RAG

*"Why did you return this document?"* is answered by a score, and the document is unchanged by having been returned. Observability is a debugging convenience.

*"Why do you believe this about me?"* is a question a **user** asks, about a claim the system made in the first person, and the answer has to be a provenance chain rather than a number. It is also the question a regulator asks, which makes it a requirement rather than a convenience — and it must be answerable years later, about a belief that has since been retired.

## Mechanism

**The chain is walkable because nothing on it was destroyed.** `supersession-not-deletion` argued that from an audit angle two levels ago; this is that argument cashed. A retired belief still holds its `superseded_by`, so *"what did you think before, and what changed your mind?"* is a pointer traversal.

**The explanation surfaces things nobody would look for.** Northwind was retired by *"Priya is a staff engineer"* — not by *"Priya works at Calico Systems"*, which is the belief a reader would assume. Both arrived in session 8 and arbitration compared the pair it compared. Nothing is wrong, and **nobody would ever have found out** without asking the record directly.

**A memory diff is what a write actually did.**

```
turn  1 s1   {'added': 2, 'removed': 0, 'retired': 0}
turn 14 s8   {'added': 4, 'removed': 0, 'retired': 1}
turn 18 s10  {'added': 1, 'removed': 0, 'retired': 1}
turn 22 s12  {'added': 2, 'removed': 0, 'retired': 0}
```

`removed` is zero on every turn of the corpus, and that is the invariant worth watching rather than the additions. Nothing should ever be removed by a write — only retired — so a non-zero `removed` is either a deletion request or the `background-job-mechanics` lost update, and those are the two events you want an alert on.

### Three questions the record cannot answer

```
which memories were in the context when the assistant said that?
how often has this belief actually been used?
which query surfaced it?
```

All three need something written at **read** time, and the store's design cannot supply them however carefully it carries provenance. `access_count` exists on the record and is **0 on all 37 memories** — the field was there and nothing ever wrote to it.

Listing them is the point. An observability story claiming full coverage from provenance alone is wrong in a way nobody notices until an incident.

## Design decisions

**Why reconstruct rather than log?** Because a log is a second source of truth that drifts, and most of these answers cannot drift — they are fields on the record being explained. Logging the same facts would create a copy that can disagree with the store about the store.

**Why is `removed` in the diff when it is always zero?** Because it is an assertion. `temporal-knowledge-graphs` made this argument about cascade counts and `rtbf-and-auditability` about deletion receipts: a number that is always zero is worth printing precisely because the day it is not is the day something is wrong.

**Why not implement the retrieval log?** Because it is a genuine write on the read path — the one path this course has kept free of writes — and its cost, retention and privacy consequences are a design exercise of their own. What this lesson delivers is the boundary: six kinds answerable now, three needing a decision nobody has made.

## Lab

**You'll implement:** `explain`, `diff`, and `unanswerable`.

**Run:**
```
uv run python curriculum/advanced/memory-observability/lab/lab.py
```

**Expected output:** two explanations — one open-ended belief and one retired, with its supersession named — the per-turn diff showing **`removed: 0`** throughout, `access_count` at **0 of 37**, and the three unanswerable questions.

**Stretch:** find which belief retired *"Priya is vegetarian"* and check whether it is the one you expected. **A provenance chain is most useful exactly where it disagrees with your assumption, which is why it has to be readable rather than reasoned about.**

## What this adds to the capstone

`memlab.production.observe` — `Explanation`, `explain`, `diff`, `unanswerable`. Reads only fields the record already carries; adds no logging.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| "Why do you think that?" unanswerable | Provenance not written at ingest | Ask a belief for its source turn | Provenance on the record |
| Chain breaks at a retirement | Superseded beliefs destroyed | Follow `superseded_by` backwards | Retire, never delete |
| Log disagrees with the store | Second source of truth | Compare a log line to the record | Reconstruct, do not log |
| Silent data loss | `removed` not watched | Diff a write; check `removed` | Assert it stays zero |
| Coverage overstated | Read-time questions assumed covered | Ask what was in the context | List the unanswerable |

## Check yourself

??? question "The record answers six kinds of question with no logging. Why not the other three?"
    Because they are about the **read**, and reads currently write nothing. What was in the context, how often a belief was used, which query surfaced it — none is a property of the memory, all are properties of an event that happened to it. `access_count` is on the record and reads 0 on all 37 memories: the field was designed for this and no stage ever wrote to it.

??? question "Northwind was retired by "staff engineer" rather than by "works at Calico". Is that a bug?"
    No — both arrived in session 8, both claim the employer slot, and arbitration compared the pair conflict detection handed it. The belief that ends up as `superseded_by` is whichever won that comparison, and the outcome is correct. What matters is that nobody would ever have discovered this by reasoning about the code, which is the argument for making the chain readable.

??? question "Why print `removed` when it is zero on every turn?"
    Because the zero is the claim. Writes should only ever add and retire; a removal means either a deletion request or the lost update that `background-job-mechanics` measured, and both are events worth an alert. A field that is always zero costs nothing to print and is the only warning you will get.

## Connections

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [The Failure Field Guide](../failure-field-guide/index.md)

**Concepts assumed:** [Provenance](../../../concepts/provenance.md) · [Bi-Temporal Modeling](../../../concepts/bi-temporal-modeling.md) · [Derivation Graph](../../../concepts/derivation-graph.md)

**This unlocks:** [Invariants and Drift Detection](../invariants-and-drift-detection/index.md)
<!-- graph:end -->
