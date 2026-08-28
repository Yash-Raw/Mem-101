---
id: capstone-finale
title: "Hardening Pass"
level: advanced
stage: govern
estimated_minutes: 50
concepts_taught: [release-report, open-item]
concepts_required: [store-invariant, cost-profile, benchmark-claim]
lessons_required: [schema-migration-on-live-memory]
capstone_piece: memlab.production.release
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Hardening Pass

> **In one line.** Eighty-four lessons, three passing exams, and six things that are still wrong — and the last section is what makes the first two worth reading.

## Where this sits

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~50 min**

**You need first:** [Migrating Live Memory](../schema-migration-on-live-memory/index.md)

**Concepts assumed:** [Store Invariant](../../../concepts/store-invariant.md) · [Cost Profile](../../../concepts/cost-profile.md) · [Benchmark Claim](../../../concepts/benchmark-claim.md)
<!-- graph:end -->

## The problem

A release report is where a system stops being a set of lessons and becomes something a person might deploy. The temptation is to report what works.

```
memlab v0.3 — 84 lessons, 742 tests

  exams
    belief          passes from @I4
    context (k=5)   passes from @I6
    budgeted        51 tokens from @I8; derived floor 43

  cost
    write path      2.0 model calls and 1.6 embeddings per turn
    read path       no model calls; 2 embeddings warm
    blocking        50% of per-turn cost; the other half is deferred

  open (6)
    extraction          a conditional clause is dropped; the reason a step matters is lost
    vocabulary          9 of 37 memories claim no modelled slot, so nothing can contradict them
    extraction leakage  a deleted record's timestamp survives in four others with no edge to follow
    observability       what was in the context is unrecorded; access_count is 0 of 37
    consolidation cost  candidate pairs grow 104x for 8x the store
    evaluation          1 of 4 component metrics distinguishes any two profiles
```

**A release report with no open items is a release report nobody checked.**

## Why this isn't RAG

A retrieval system ships against a benchmark: a score on a shared corpus, comparable to somebody else's score. It is a weak claim and it is *legible*, and there is an industry-wide agreement about what it means.

There is no such agreement here, and `reading-benchmark-claims` measured why — memory benchmarks share neither their corpora nor their division of labour with the reading model. So the honest release artifact is not a number. It is **the measurements plus the gaps**, each naming the lesson that found it, so that a reader can check any claim and see the shape of what was not attempted.

## Mechanism

**Every open item is a measurement, not a worry.** Each cites the lesson that hit it in a running system, and each carries a number: one conditional clause in twenty-four turns, nine unnameable memories, four records carrying a deleted timestamp, 104× candidate pairs, one informative metric of four. **A gap without a number is a feeling** — and writing this report is what forced two of the six to acquire theirs.

**The three exams answer different questions, and all three are needed.** `belief-and-context-exams-can-disagree` is a test in the capstone suite for a reason: the store can hold the right answer and never say it. The budgeted exam adds a third — it can say it and not fit.

**`complete` returns true when there *are* open items.** That is not a joke about software. A release whose gap list is empty has either had no one look at it or has stopped being examined, and both are worse than six named problems with numbers attached.

### What the course actually established

Three claims survived every measurement, and none was obvious at the start:

- **The write path dominates**, and the read path makes no model calls at all — a design outcome of decisions argued on correctness grounds, not an optimisation.
- **Similarity cannot carry any of the write path's decisions.** It cannot generate conflict candidates, identify corroboration, or find a procedure. Every stage that works is keyed on structure — the `SLOT` table, which nine modules outside its own now import.
- **Most of the interesting results are null results.** Reflection made the answer worse; three of I8's four mechanisms moved nothing; the graph has one node; per-type scheduling barely helped. **The measurement that says "this did nothing" is the one that saves the next person a month.**

## Design decisions

**Why does the report take `lessons` and `tests` as arguments?** Because they change, and a report that hardcodes them is stale on the next commit. Everything else is a claim about the system's behaviour, which is pinned by tests and does not move without a reason.

The count is **test functions**, read from source — parametrised cases expand to more at collection time, and the lab counts definitions because it is itself run by the suite and cannot shell out to pytest without recursing.

**Why name a lesson beside each gap rather than a ticket?** Because the lesson contains the measurement and the reproduction. A ticket says what to do; the lesson says how the problem was found and what it cost, which is what someone picking it up in six months actually needs.

**Why is "1 of 4 metrics is informative" an open item rather than a caveat?** Because it is a defect in the evaluation, and evaluations are part of the system. Three saturated metrics mean the next change to extraction, resolution or arbitration will be measured by something that cannot move — which is a gap in exactly the sense the others are.

## Lab

**You'll implement:** `report`, `unfinished`, and `lines`.

**Run:**
```
uv run python curriculum/advanced/capstone-finale/lab/lab.py
```

**Expected output:** the release report — three exams, three cost lines, and **6** open items, each naming the lesson that measured it.

**Stretch:** delete the `open_items` and re-read the report. It is shorter, stronger-sounding, and every remaining line is still true. **That version is the one that gets published, and it is the reason `reading-benchmark-claims` exists.**

## What this adds to the capstone

`memlab.production.release` — `Release`, `report`, `unfinished`, `lines`. **The course ends here.** `memlab` v0.3: bi-temporal, multi-agent, governed, measured, with deletion that reaches every structure and a written list of what it still gets wrong.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Release report with no gaps | Reporting what works | Ask what is still wrong | Gaps are a required section |
| Gaps that cannot be acted on | Worries rather than measurements | Ask for the number | Cite the measurement |
| Report stale after one commit | Counts hardcoded | Re-run it | Pass what changes |
| Claim nobody can check | Score with no reproduction | Try to reproduce it | Name the lesson |
| Saturated metrics guarding a change | Evaluation treated as external | Ask which metric would move | Gaps include the eval |

## Check yourself

??? question "Why is a release with six open items better than one with none?"
    Because the six are measured, numbered and attributed, which means someone examined the system closely enough to find them. An empty list means either nobody looked or the looking stopped being reported — and the failure mode of the second is that the gaps still exist and are now undocumented.

??? question "Three of the biggest findings in this course are null results. Why do they belong in a release report?"
    Because they are the expensive knowledge. *Reflection makes the budgeted answer worse* and *three of four packing mechanisms move nothing* are results nobody can get without building the thing and measuring it, and they are what stops the next person spending a month on a mechanism that has already been shown not to pay.

??? question "What would you build next, given the open list?"
    Extraction. It drops the conditional clause that explains a procedure, its parser leaks a deleted record's timestamp into four others, and it is the entire blocking half of the per-turn cost — so two of the six items are the same stage seen from different lessons, and the cost argument points at it too. That overlap is the kind of thing only a collected list makes visible; from inside either lesson it looks like a local problem.

    Note what is *not* on that list: the nine unnameable memories are a gap in the `SLOT` table's coverage, not in extraction. The memories were extracted correctly and there is no attribute to file them under.

## Connections

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~50 min**

**You need first:** [Migrating Live Memory](../schema-migration-on-live-memory/index.md)

**Concepts assumed:** [Store Invariant](../../../concepts/store-invariant.md) · [Cost Profile](../../../concepts/cost-profile.md) · [Benchmark Claim](../../../concepts/benchmark-claim.md)
<!-- graph:end -->
