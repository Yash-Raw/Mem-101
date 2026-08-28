---
id: component-metric
title: "Component Metric"
kind: concept
stage: govern
contrasts_with: [absent-corpus]
related: [unlocated-assertion, slot, provenance]
status: published
---

# Component Metric

A score for one stage of the pipeline, checked against the answer key rather than through the final answer.

## Why it matters in a memory layer

One end-to-end boolean over seven stages can detect a regression and never locate one. Component metrics attribute it — and they are **code**, written against a key someone phrased for a human reader, so they are wrong first and wrong in the direction that looks like a system problem.

On this course, the first version reported **0.733**, **0.600** and **0.500** across three stages, and every number was the metric: it matched gold's paraphrases as substrings, ignored the session gold provides to disambiguate, and required every claim in a slot to be retired when one of them was correctly still live.

Locate by **session and slot**, never by the key's prose. Print what the metric located, not just the score — every one of those bugs was invisible in the number and obvious in the intermediate result.

## Connections

<!-- graph:begin -->
**Taught in:** [Component Metrics](../curriculum/advanced/component-metrics/index.md)

**Used in:** [Build Your Own Harness](../curriculum/advanced/end-to-end-eval/index.md)

**Do not confuse with:** [The Absent Corpus](absent-corpus.md)
<!-- graph:end -->
