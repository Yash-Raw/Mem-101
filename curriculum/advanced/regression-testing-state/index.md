---
id: regression-testing-state
title: "Regression Testing a Stateful System"
level: advanced
stage: govern
estimated_minutes: 45
concepts_taught: [pinned-assertion, golden-conversation]
concepts_required: [eval-suite, flat-metric, memory-record]
lessons_required: [end-to-end-eval]
capstone_piece: memlab.eval.regression
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Regression Testing a Stateful System

> **In one line.** This repository has a 376-assertion regression suite that nobody designed — it was assembled one lesson at a time by writing down what was measured.

## Where this sits

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [Build Your Own Harness](../end-to-end-eval/index.md)

**Concepts assumed:** [Eval Suite](../../../concepts/eval-suite.md) · [Flat Metric](../../../concepts/flat-metric.md) · [The Memory Record](../../../concepts/memory-record.md)

**This unlocks:** [LLM as Judge, and Its Failure Modes](../llm-as-judge-for-memory/index.md)
<!-- graph:end -->

## The problem

`end-to-end-eval` compares profiles at one moment. The harder question is comparing the **same** profile across time: does the change you are about to make move something you were not thinking about?

Count what already stands in the way:

```
lab test files      84
capstone test files 3
test functions      752
pinned literals     376   (50% of tests)
module snapshots    17
```

**Half the tests in this course assert against a literal number.** Not by policy — because a memory system's outputs are counts, ranks and scores rather than pass/fail, so writing down what you measured *is* the test.

## Why this isn't RAG

A retrieval system is close to stateless between queries: the same query against the same index gives the same result, and a regression test is a fixture and an expected ranking.

A memory layer's state is the accumulated product of every write that came before, so a regression is not *"this query changed"* but *"the store is different, and something I measured three modules ago no longer holds"*. The blast radius of a write-path change is every number anyone has ever quoted — and this course has quoted a lot of them.

## Mechanism

**Pinned assertions are snapshots of behaviour.** `assert len(store.all()) == 37` is not a specification; it is a record of what the system did when someone last looked. That is exactly what you want from a regression guard and exactly what you do not want from a spec, and confusing the two is how a pinned number becomes a requirement nobody chose.

**Module snapshots make a regression attributable.** Seventeen checkpoints, and `at("I3")` is the system as I3 left it — so a moved number can be bisected rather than reasoned about. Every measured claim in this course is anchored to one, which is why *"I3's dedupe changed the store size"* did not silently invalidate every count I1 quoted.

**A golden conversation is what makes 376 literals tolerable.**

```
376 pinned literals are only maintainable against a fixed corpus;
with a changing one, each is two claims at once
```

With a deterministic corpus a pinned literal is a claim about the system. Without one it is a claim about the corpus *and* the system, failing on every ingest for reasons nobody can attribute — and the rational response is to delete the assertions, which removes the only regression suite there was.

**The suite is emergent, and that is a weakness as well as a strength.** Nobody chose which 376 numbers to pin, so coverage follows whatever each lesson happened to measure. `end-to-end-eval` found three component metrics flat across every profile; the pinned literals have the same property and no report that surfaces it.

## Design decisions

**Why not replace pinned literals with tolerances?** Because a tolerance is a decision about how much drift is acceptable, made once, applied everywhere, by someone who cannot know which numbers matter. `promotion-as-release` measured a change that cost five tokens of headroom — 51 to 56 — and that was the whole result; a ±10% tolerance would have hidden it. Determinism makes exactness affordable, so exactness is the right default.

**Why keep the count of pinned assertions rather than a list?** Because the list is the test files, and duplicating it produces a second thing to maintain that disagrees with the first. The count is a health signal — if it stops growing while lessons are added, the new lessons are not writing down what they measured.

**Why is `inventory` a read of the source rather than a pytest plugin?** Because it must be answerable without running anything. *"How much is guarded?"* is a question you ask before making a change, and a plugin answers it only after the suite has already passed.

## Lab

**You'll implement:** `inventory` and `golden_conversation_required`.

**Run:**
```
uv run python curriculum/advanced/regression-testing-state/lab/lab.py
```

**Expected output:** **84** lab test files, **3** capstone files, **752** test functions, **376** pinned literals at **50%**, and **17** module snapshots.

**Stretch:** change one number in `capstone/fixtures/corpus.jsonl` — a timestamp will do — and run the suite. Dozens of assertions fail across lessons that have nothing to do with each other, and none of the failures names the corpus. **A golden conversation is load-bearing in proportion to how many numbers you pinned against it.**

## What this adds to the capstone

`memlab.eval.regression` — `Inventory`, `inventory`, `golden_conversation_required`. Reads the test sources; runs nothing.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Numbers updated to match a change | Pinned literal read as a spec | Ask what the number was measuring | Bisect against a snapshot |
| Assertions deleted en masse | Corpus changed; literals now unmaintainable | Count failures after a fixture edit | A frozen corpus |
| Regression detected, not attributable | No per-module checkpoints | Try to bisect a moved number | Module snapshots |
| Real regression inside a tolerance | Drift budget applied uniformly | Ask what change the tolerance hides | Exactness plus determinism |
| Coverage assumed from the count | The suite is emergent | Check which stages are pinned | Report what never moves |

## Check yourself

??? question "Half the tests assert a literal number. Is that a smell?"
    It is the shape the problem forces. A memory system emits counts, ranks and token budgets, so the only faithful record of correct behaviour is the number that was measured — and this course's most valuable findings were exactly such numbers. The smell would be *updating* them to match a change, which is why every one is anchored to a module snapshot that can be bisected instead.

??? question "Why does a fixed corpus matter more here than in a stateless system?"
    Because a pinned literal is a joint claim about the system and its input. Freeze the input and the claim is about the system alone, which is checkable. Let the input drift and every one of the 376 assertions fails periodically for unattributable reasons, and the rational response — deleting them — removes the entire regression suite.

??? question "The suite was never designed. What is missing because of that?"
    A statement of what it does *not* cover. Coverage followed whatever each lesson happened to measure, so the pinned literals cluster where numbers were interesting and thin out where behaviour was obviously correct — the same shape `end-to-end-eval` found in the component metrics, with no report that surfaces it. The count is a health signal, not a coverage claim.

## Connections

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [Build Your Own Harness](../end-to-end-eval/index.md)

**Concepts assumed:** [Eval Suite](../../../concepts/eval-suite.md) · [Flat Metric](../../../concepts/flat-metric.md) · [The Memory Record](../../../concepts/memory-record.md)

**This unlocks:** [LLM as Judge, and Its Failure Modes](../llm-as-judge-for-memory/index.md)
<!-- graph:end -->
