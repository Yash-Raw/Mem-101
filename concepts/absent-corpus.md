---
id: absent-corpus
title: "The Absent Corpus"
kind: concept
stage: govern
contrasts_with: [moving-ground-truth]
related: [extraction, memory-record, provenance]
status: published
---

# The Absent Corpus

There is no pre-existing document collection to judge against — the system under test produced the thing being evaluated.

## Why it matters in a memory layer

A retrieval benchmark works because someone judged document 47 relevant to query 12 before any system existed. The judgement stays true, every system is scored against the same fixed pair, and precision and recall mean something because **the set of correct answers is a property of the data**.

Here the "documents" are memories the system created by deciding what was worth keeping. So the labels are claims about what the system *should have decided*, written by hand — and if they are written after measuring, they agree with whatever was built.

This course's answer key covers **23 of 25 assertions** in machine-checkable form, and it does so only because it was written before the system. The two that are not checkable are English sentences about structures, which are real requirements and reviewer instructions rather than tests.

## Connections

<!-- graph:begin -->
**Taught in:** [Why Memory Eval Is Hard](../curriculum/advanced/why-memory-eval-is-hard/index.md)

**Used in:** [Component Metrics](../curriculum/advanced/component-metrics/index.md) · [Build Your Own Harness](../curriculum/advanced/end-to-end-eval/index.md)

**Do not confuse with:** [Moving Ground Truth](moving-ground-truth.md)
<!-- graph:end -->
