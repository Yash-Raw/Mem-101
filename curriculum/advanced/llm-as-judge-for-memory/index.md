---
id: llm-as-judge-for-memory
title: "LLM as Judge, and Its Failure Modes"
level: advanced
stage: govern
estimated_minutes: 45
concepts_taught: [judge-role, bounded-output]
concepts_required: [eval-suite, memory-operations, provenance]
lessons_required: [regression-testing-state]
capstone_piece: memlab.eval.judge
lab: lab/lab.py
lab_runtime: fake
status: published
---

# LLM as Judge, and Its Failure Modes

> **In one line.** This system calls a model in three places and exactly one is a judgement — the rule that kept it to one is why the store's contents do not depend on sampling.

## Where this sits

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [Regression Testing a Stateful System](../regression-testing-state/index.md)

**Concepts assumed:** [Eval Suite](../../../concepts/eval-suite.md) · [Memory Operations](../../../concepts/memory-operations.md) · [Provenance](../../../concepts/provenance.md)
<!-- graph:end -->

## The problem

Every model call in the capstone, and what protects its result:

```
site                    role           bounded  vs gold  repro   safe
extract/naive.py        generation       False    False   True  False
extract/pipeline.py     generation       False    False   True  False
evolve/conflict.py      judgement         True     True   True   True
```

One judgement. Two generations, whose output is filtered by later stages that do not trust it. And a rule stated in `deterministic-freshness` two levels ago:

> the model says *these two disagree*, and rules say *this one wins*

## Why this isn't RAG

Judging retrieval output is comparatively safe. The judge scores an answer against documents that exist, a human can read both, and a wrong judgement produces a wrong *number* — the corpus is unchanged and the next run re-derives everything.

A judge in a memory system decides what is **stored**. A wrong call at `conflict.classify` retires a true belief permanently, and the audit trail records that the system decided it, with no reason anyone can inspect. **The output of a judgement here is not a score, it is state.**

## Mechanism

**Three properties, and they only work together:**

| property | what it prevents |
|---|---|
| bounded output | four labels, not free text — the failure space is enumerable |
| checked against gold | the judge's calls are scored, so drift is visible |
| reproducible | fixture-backed, so two runs agree and a diff means a change |

`conflict.classify` has all three. Remove any one and the others stop helping: unbounded output cannot be scored against a key, an unchecked judge drifts invisibly, and a non-reproducible one makes every regression unattributable. **`safe` is an `and`, not a score.**

**Arbitration is never a model, and that is a rule rather than a preference.**

```
detection is a language question and may be a model; arbitration is a policy
and must not be, because its output changes what is believed and has to be
explainable
```

`evolve/arbitrate.py` decides with four ordered rules, each returning a stated reason. A model there gives a store whose contents depend on sampling, and *"why do you think that?"* — the question the entire provenance chain exists to answer — has no answer.

**The exam is not model-judged either.**

```
a judge is a second system with no ground truth of its own; when it disagrees
with the key nothing says which is wrong. The exam is checked against 75
reviewable fixtures instead
```

Seventy-five fixtures, authored with `register_fixture`, reviewable in a diff. That is more work than a judge and it is the reason every number in this course is reproducible.

## Design decisions

**Why are the generation sites marked unsafe?** Because they are, on these criteria — unbounded output, unscored against gold. What makes them acceptable is different: **nothing downstream trusts them.** The durability gate, dedupe, arbitration and the tier cap all exist because extraction over-produces, and `over-extraction` measured that in Beginner. Generation is safe when it is filtered; judgement is safe when it is bounded and checked.

**Why not add a judge for the stages that have no metric?** `dedupe`, `decay` and `rank` have no gold entries because their correctness is a policy — and a judge would supply an opinion in place of the policy, then be unfalsifiable because there is nothing to check it against. The absence of a metric is not an invitation.

**Why 75 fixtures instead of one judge call?** Because a fixture is a decision someone made once, visible in a diff, and stable forever. A judge is a decision remade on every run, invisible unless logged, and different when the model changes. The fixtures cost more to write and nothing to trust.

## Lab

**You'll implement:** `uses`, `arbitration_is_never_a_model`, and `judging_the_exam`.

**Run:**
```
uv run python curriculum/advanced/llm-as-judge-for-memory/lab/lab.py
```

**Expected output:** the three-site table with exactly one `judgement` and one `safe`, **1 of 3** calls a judgement, and **75** fixtures.

**Stretch:** mark `conflict.classify` as unbounded — free-text relations instead of four labels — and ask what `component-metrics` could still score. Nothing: arbitration's metric locates records by slot and compares against gold's four relation names. **A judgement with an open output space cannot be evaluated, which is the same sentence as "cannot be trusted".**

## What this adds to the capstone

`memlab.eval.judge` — `Role`, `Use`, `uses`, `arbitration_is_never_a_model`, `judging_the_exam`. A description of the system rather than a stage in it: the rules it states were applied two levels ago and had never been written down together.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Store contents differ between runs | A model decides what survives | Ingest twice; diff the stores | Rules for arbitration |
| "Why do you think that?" unanswerable | Judgement with no stated reason | Ask a stage for its rule | Reasons, not scores |
| Judge drifts and nobody notices | Not scored against a key | Compare the judge's calls to gold | Bounded output plus gold |
| Unfalsifiable metric | Judge supplied where no gold exists | Ask what would prove it wrong | Leave the gap visible |
| Evaluation depends on a model version | Judge instead of fixtures | Change the model; re-run | Authored fixtures |

## Check yourself

??? question "Two of the three model calls are marked unsafe. Should they be changed?"
    No — the criteria are for judgements and those are generations. Extraction is allowed to over-produce precisely because four later stages exist to filter it, which Beginner measured as necessary. The table is not a verdict on every call; it is a check that only one call *decides* anything, and that the one that does has all three protections.

??? question "Why is arbitration a rule rather than a preference?"
    Because its output is state. A model deciding which of two beliefs survives produces a store whose contents depend on sampling, so the same conversation ingested twice yields different beliefs and nothing records why. Every other decision in the system can be re-derived; this one destroys the alternative.

??? question "Seventy-five hand-authored fixtures is a lot of work. What does it buy?"
    Reproducibility, which is what every number in this course rests on. A fixture is decided once and visible in a diff; a judge is re-decided on each run and changes when the model does. Without the fixtures, the 331 pinned assertions from the previous lesson would be measuring the model's mood.

## Connections

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [Regression Testing a Stateful System](../regression-testing-state/index.md)

**Concepts assumed:** [Eval Suite](../../../concepts/eval-suite.md) · [Memory Operations](../../../concepts/memory-operations.md) · [Provenance](../../../concepts/provenance.md)
<!-- graph:end -->
