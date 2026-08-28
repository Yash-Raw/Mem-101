---
id: failure-field-guide
title: "The Failure Field Guide"
level: advanced
stage: govern
estimated_minutes: 45
concepts_taught: [failure-class, differential-diagnosis]
concepts_required: [consistency-window, unnameable-claim, cascade-deletion]
lessons_required: [scaling-the-store]
capstone_piece: memlab.production.failures
lab: lab/lab.py
lab_runtime: fake
status: published
---

# The Failure Field Guide

> **In one line.** Five of the seven production symptoms have more than one cause, so the useful column is not the cause — it is the measurement that separates them.

## Where this sits

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [Scaling the Store](../scaling-the-store/index.md)

**Concepts assumed:** [Consistency Window](../../../concepts/consistency-window.md) · [Unnameable Claim](../../../concepts/unnameable-claim.md) · [Cascade Deletion](../../../concepts/cascade-deletion.md)
<!-- graph:end -->

## The problem

Beginner catalogued seven failures of a naive system. These are the other seven — the ones that appear *after* it works:

```
the assistant argues with a correction              2 causes
a fact the user gave is never recalled              3 causes
the answer is right and the context is wrong        2 causes
deleted data reappears                              2 causes
half the store stops being retrievable              1 cause
writes disappear during a batch                     1 cause
a metric improves and nothing got better            2 causes

failures with more than one cause: 5 of 7
measured somewhere in the course : 7 of 7
```

**A production failure is identified by what the user sees, not by which component is wrong.** *"A fact I told you is never recalled"* has three causes in three different stages, and the symptom is identical in all three.

## Why this isn't RAG

A retrieval failure is usually diagnosable from one artifact: the ranked list. The document is missing, or it is there and ranked low, and either way the question *"why didn't it come back?"* is answered by inspecting one thing.

Here the answer to *"why wasn't it recalled?"* lives in a different stage depending on the case — the extractor, the slot table, or the tier cap — and the store looks the same from the outside in all three. **The read path is the last place to look**, and it is the only place a retrieval intuition suggests looking.

## Mechanism

**The `tell` column is the lesson.** Every row names a measurement that discriminates, and each is cheap:

| symptom | the tell |
|---|---|
| argues with a correction | replay turn by turn, diff against an eager store |
| a fact is never recalled | check the store, then `slot_of`, then the eligible pool |
| answer right, context wrong | compare the belief exam with the context exam |
| deleted data reappears | re-scan every structure by id |
| half the store unretrievable | compare the eligible pool before and after a write |
| writes vanish in a batch | add a memory mid-job and count it afterwards |
| metric up, nothing better | check whether the metric moved *at that change* |

**Three of these are ordered, not parallel.** *"Never recalled"* is checked in sequence — is it in the store at all; if so does it claim a slot; if so is it in the eligible pool — because each answer makes the next question meaningful. A guide that lists three causes without the order sends you to read the ranking code first, which is where none of the three lives.

**All seven were measured, none were predicted.** Every row cites the lesson that hit it — the consistency window, the unnameable agent writes, the eligible pool collapsing after one future-dated write, the memories a batch job destroyed. **This is a field guide because it is a list of things that already happened**, not a taxonomy someone sat down and derived, and a test checks that every cited lesson exists.

## Design decisions

**Why organise by symptom rather than by stage?** Because a stage-organised guide is only usable by someone who already knows which stage is at fault, which is the thing they are trying to find out. The symptom is what arrives — from a user, from a support ticket, from your own use — and it is almost always ambiguous.

**Why keep the single-cause rows?** Because they are the ones where the tell is *conclusive*, and knowing which two of seven those are is worth as much as the ambiguous ones. If half the store stops being retrievable, there is one thing to check.

**Why cite the lesson rather than the fix?** Because the fix is in the code and the measurement is not. Six months from now the question is *"how do I tell?"*, and the answer is a procedure — the lesson is where that procedure was run against a system that actually exhibited the failure.

## Lab

**You'll implement:** `field_guide`, `ambiguous`, and `coverage`.

**Run:**
```
uv run python curriculum/advanced/failure-field-guide/lab/lab.py
```

**Expected output:** seven symptoms with their causes and tells, **5 of 7** ambiguous, and **7 of 7** citing a lesson that measured them.

**Stretch:** reorganise the guide by stage instead of symptom. *"A fact is never recalled"* splits across three entries under extract, evolve and forget, and none of them is findable from what the user reported. **A taxonomy is indexed by the answer; a field guide has to be indexed by the question.**

## What this adds to the capstone

`memlab.production.failures` — `Failure`, `field_guide`, `ambiguous`, `coverage`. Every entry names the lesson that measured it, so the guide is checkable against the course rather than assertable.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Debugging starts at the read path | Retrieval intuition applied | Ask which stage the symptom implicates | Symptom-indexed guide |
| Causes listed without an order | Parallel list of three | Try to act on the guide | Order the checks |
| A guide of hypotheticals | Written from reasoning, not incidents | Ask which were observed | Cite the measurement |
| One cause assumed | The symptom is ambiguous | Count causes per symptom | Report ambiguity |
| Fix documented, tell forgotten | The code records the fix | Ask "how would I know?" | Record the procedure |

## Check yourself

??? question ""A fact I told you is never recalled" — where do you look first?"
    The store, and it is the least interesting of the three answers. If the fact is there, the next question is whether it claims a slot, because an unnameable memory is never arbitrated and never surfaces for a question about that attribute; and if it does, whether it is in the eligible pool, because the tier cap may have demoted it. The order matters — reading the ranking code is what a retrieval intuition suggests and the answer is never there.

??? question "Why does this guide only contain failures that were measured?"
    Because a guide of predicted failures is a list of worries, and its entries have no tell — nobody has had to distinguish them. Every row here cites the lesson that hit the failure in a running system, which is also what makes the `tell` column trustworthy: it is the measurement that actually resolved the case.

??? question "Two symptoms have a single cause. Is that column doing any work?"
    Yes, and it is the part that saves the most time. Ambiguity tells you to run a sequence; a single cause tells you to check one thing and be done. Knowing that *"half the store stopped being retrievable"* has exactly one explanation is a stronger statement than any of the multi-cause rows.

## Connections

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [Scaling the Store](../scaling-the-store/index.md)

**Concepts assumed:** [Consistency Window](../../../concepts/consistency-window.md) · [Unnameable Claim](../../../concepts/unnameable-claim.md) · [Cascade Deletion](../../../concepts/cascade-deletion.md)
<!-- graph:end -->
