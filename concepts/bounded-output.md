---
id: bounded-output
title: "Bounded Output"
kind: concept
stage: govern
contrasts_with: [judge-role]
related: [component-metric, pinned-assertion, golden-conversation]
status: published
---

# Bounded Output

A model judgement restricted to a fixed set of labels, so that it can be scored at all.

## Why it matters in a memory layer

Three properties make a model judgement acceptable, and they only work together: the output is **bounded**, the calls are **checked against a key**, and the run is **reproducible**. Remove any one and the others stop helping — unbounded output cannot be scored against a key, an unchecked judge drifts invisibly, and a non-reproducible one makes every regression unattributable. It is an `and`, not a score.

On this course the single judgement site returns one of four relation labels, is scored by a component metric against `gold.yml`, and is fixture-backed. Widen it to free text and the metric has nothing to compare, which is the same sentence as *cannot be trusted*.

The alternative to a judge is authored fixtures: **75** here, each a decision made once and visible in a diff, rather than one remade on every run and different when the model changes. Without them the course's 331 pinned assertions would be measuring the model's mood.

## Connections

<!-- graph:begin -->
**Taught in:** [LLM as Judge, and Its Failure Modes](../curriculum/advanced/llm-as-judge-for-memory/index.md)

**Do not confuse with:** [Judge Role](judge-role.md)
<!-- graph:end -->
