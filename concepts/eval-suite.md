---
id: eval-suite
title: "Eval Suite"
kind: concept
stage: govern
contrasts_with: [component-metric]
related: [flat-metric, moving-ground-truth, absent-corpus]
status: published
---

# Eval Suite

One battery run across every version of the system, so a claim that a module improved something is checkable rather than remembered.

## Why it matters in a memory layer

A retrieval leaderboard compares *systems* on a corpus somebody else built. Here the comparison is between **versions of one system**, and each version produces the corpus differently — so every profile must be built from scratch. Share a store between two and the later one inherits the earlier one's write path and reports an improvement it did not make.

The result on this course is humbling and precise: across six profiles and eight columns, the battery distinguishes **three**. Extraction, resolution and arbitration were already correct before Level 3 began; one component metric moves, at the module that built it; the token budget captures two more.

Print the empty regression list. Six rows and eight columns is more than anyone checks by eye, and the whole snapshot discipline exists because a later module can silently move an earlier one's number.

## Connections

<!-- graph:begin -->
**Taught in:** [Build Your Own Harness](../curriculum/advanced/end-to-end-eval/index.md)

**Used in:** [LLM as Judge, and Its Failure Modes](../curriculum/advanced/llm-as-judge-for-memory/index.md) · [Reading Benchmark Claims Critically](../curriculum/advanced/reading-benchmark-claims/index.md) · [Regression Testing a Stateful System](../curriculum/advanced/regression-testing-state/index.md)

**Do not confuse with:** [Component Metric](component-metric.md)
<!-- graph:end -->
