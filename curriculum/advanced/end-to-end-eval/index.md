---
id: end-to-end-eval
title: "Build Your Own Harness"
level: advanced
stage: govern
estimated_minutes: 50
concepts_taught: [eval-suite, flat-metric]
concepts_required: [component-metric, unlocated-assertion, absent-corpus]
lessons_required: [component-metrics]
capstone_piece: memlab.eval.suite
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Build Your Own Harness

> **In one line.** Run the whole battery across six profiles and it distinguishes three of them — most of Level 3 is invisible to every metric in it.

## Where this sits

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~50 min**

**You need first:** [Component Metrics](../component-metrics/index.md)

**Concepts assumed:** [Component Metric](../../../concepts/component-metric.md) · [Unlocated Assertion](../../../concepts/unlocated-assertion.md) · [The Absent Corpus](../../../concepts/absent-corpus.md)

**This unlocks:** [Regression Testing a Stateful System](../regression-testing-state/index.md)
<!-- graph:end -->

## The problem

Every claim in this course has the form *"this module improves X"*, and until now the evidence was a lesson quoting two numbers measured by hand at different times. A suite runs the same battery over every profile and puts them in one table:

```
profile    mem  live  belief  budget    extract    resolve  arbitrate     anchor
I4          37    30    True    None      1.000      1.000      1.000      0.000
I6          37    30    True      77      1.000      1.000      1.000      0.000
I8          37    30    True      51      1.000      1.000      1.000      0.000
A1          37    30    True      51      1.000      1.000      1.000      1.000
A2          37    30    True      51      1.000      1.000      1.000      1.000
A3          37    30    True      51      1.000      1.000      1.000      1.000

flat across every profile: ['extract', 'resolve', 'arbitrate']
regressions: []
```

## Why this isn't RAG

A retrieval leaderboard compares *systems* on a fixed corpus, and every system sees the same queries and the same judgements. Comparison is the easy part; the corpus and the labels were the expensive part and someone else paid for them.

Here the comparison is between **versions of one system**, and the corpus is produced differently by each. Running a battery means building each profile from scratch — share a store between two and the later one inherits the earlier one's consolidation and reports an improvement it did not make.

## Mechanism

**A flat column is not a passing grade.** `extract`, `resolve` and `arbitrate` report 1.000 for every profile from I4 onwards. They were already correct before Level 3 started, so **they cannot justify anything built in it** — and a report that shows only the final row reads as though they could.

**Exactly one component metric moves.** `anchor` goes 0.000 → 1.000 at A1, precisely where the relative-time parser landed. Everything else in Level 3 is invisible to the component battery.

**The budget captures the other two.** `lowest_budget` goes `None` → 77 at I6, → 51 at I8, and flat thereafter — so between them the two kinds of metric distinguish **three of six profiles**: I6, I8 and A1.

### Why A2 and A3 are invisible, and what that means

They are not unmeasured because nobody tried. They are properties this shape of battery cannot express:

- **A2** is about *when* consolidation runs. Its result — a store that is wrong for a stretch of turns versus one that never is — only exists during a turn-by-turn replay; a battery over a finished ingest sees the converged store, which is identical either way. A2 measured that itself, and the identity was the finding.
- **A3** is about *rejected* writes. Every write the corpus contains is legitimate, so `@A3` is identical to `@A2` by construction — the whole demonstration is in what the policy refuses, and nothing refused is in the store to score.

**A metric that cannot see a change is not evidence the change did nothing.** It is evidence about the metric, and the suite's job is to make that distinction visible instead of leaving it in a paragraph.

## Design decisions

**Why build each profile from scratch?** Because consolidation is the expensive stage and the tempting optimisation is to ingest once and re-score. That silently gives every profile the last one's write path, and the resulting table shows uniform improvement with no cause.

**Why report `regressions` explicitly when the list is empty?** Because an empty list is a claim, and the alternative is a reader comparing eight columns across six rows by eye. It is also the check that matters most as the course grows — the whole snapshot discipline exists because a later module can move an earlier module's number.

**Why include metrics known to be flat?** Because dropping them makes the battery look sharper than it is. Three columns of 1.000 are the honest report that most of this system was already correct before most of this course, and that the exam and the budget carried the rest.

## Lab

**You'll implement:** `run`, `flat`, and `regressions`.

**Run:**
```
uv run python curriculum/advanced/end-to-end-eval/lab/lab.py
```

**Expected output:** the six-row table, `anchor` moving from **0.000** to **1.000** at A1, `budget` from `None` to **77** to **51**, three flat columns, and **no regressions**.

**Stretch:** ingest once and re-score each profile against that single store. Every column reports 1.000 from I4 onward, `anchor` included — because the store was built by the latest write path. **A harness that shares state between profiles measures the last profile six times.**

## What this adds to the capstone

`memlab.eval.suite` — `Row`, `run`, `flat`, `regressions`. Composes `eval.components` and `eval.exam` over `pipeline.at`, and builds every profile independently.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Uniform improvement, no cause | One store shared between profiles | Compare a profile's store to an earlier one | Build each from scratch |
| A metric cited as evidence for a module | Column flat across all profiles | Check whether it moved at that module | Report flatness |
| Change looks like it did nothing | The battery cannot express it | Ask what shape the change has | Name the unmeasurable |
| Regression found by eye | Eight columns, six rows | Diff consecutive rows in code | An explicit check |
| Battery looks sharper than it is | Flat columns dropped from the report | Count columns that ever move | Keep them |

## Check yourself

??? question "Three columns report 1.000 for every profile. Should they be removed?"
    No — they are the finding. Extraction, resolution and arbitration were already correct at I4, which means nothing built afterwards can be justified by them, and a report showing only the last row would let them read as evidence for the whole course. Keeping them makes the shape of the improvement visible: two modules moved the budget, one moved the parser, and the rest of the battery watched.

??? question "A2 and A3 show no change anywhere. Did they do nothing?"
    They did things this battery cannot express. A2's result exists only during a turn-by-turn replay — over a finished ingest the converged store is identical either way, which A2 measured and reported as its central finding. A3's whole demonstration is in writes that were *refused*, and a refused write is not in the store to be scored. The suite's value here is stating that precisely rather than leaving the reader to assume.

??? question "Why is an empty `regressions` list worth printing?"
    Because it is an assertion rather than an absence. Six rows and eight columns is more than anyone checks reliably by eye, and the entire snapshot discipline in this course exists because a later module can silently move an earlier module's number. An empty list is the machine saying it looked.

## Connections

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~50 min**

**You need first:** [Component Metrics](../component-metrics/index.md)

**Concepts assumed:** [Component Metric](../../../concepts/component-metric.md) · [Unlocated Assertion](../../../concepts/unlocated-assertion.md) · [The Absent Corpus](../../../concepts/absent-corpus.md)

**This unlocks:** [Regression Testing a Stateful System](../regression-testing-state/index.md)
<!-- graph:end -->
