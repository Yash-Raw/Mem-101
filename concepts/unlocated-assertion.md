---
id: unlocated-assertion
title: "Unlocated Assertion"
kind: concept
stage: govern
contrasts_with: [component-metric]
related: [moving-ground-truth, absent-corpus]
status: published
---

# Unlocated Assertion

A gold entry the metric could not find a record for — which says nothing about the system and must not be scored as a failure.

## Why it matters in a memory layer

A retrieval metric compares two sets of ids; there is no locating step and therefore no way for it to fail. Here every entry is a description of something the system was supposed to decide, and finding the record it refers to is a separate operation that can go wrong.

Fold those into the denominator and a working system reports **0.800** and **0.667** — numbers that look like regressions, stay stable across runs, and break no test, because they are internally consistent.

Report `correct`, `located` and `entries` separately. On this course three of the key's entries are genuinely unlocatable: one phrase sits inside a *question* and questions produce no memories, one entry has no time phrase at all and says so, and one names a change the system models as a past-tense statement rather than a supersession. All three are defensible; none is a failure.

## Connections

<!-- graph:begin -->
**Taught in:** [Component Metrics](../curriculum/advanced/component-metrics/index.md)

**Do not confuse with:** [Component Metric](component-metric.md)
<!-- graph:end -->
