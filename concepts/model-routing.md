---
id: model-routing
title: "Model Routing"
kind: concept
stage: govern
contrasts_with: [cache-key]
related: [latency-budget, extraction-pipeline, judge-role]
status: published
---

# Model Routing

Sending cheap, bounded work to a cheap model — and checking there is a call to route at all.

## Why it matters in a memory layer

The profile points at one target. Extraction is **81% of the per-turn cost** and has exactly the shape small models suit: bounded output, a schema, no judgement about policy. Everything else on the write path either is not a model call or must not be.

That second clause is the one to check first. Arbitration looks like an obvious routing candidate and makes **no model call** — `deterministic-freshness` made it rules two levels earlier, because its output changes what is believed and has to be explainable. Routing a stage that calls nothing is a config change with no effect and a plausible story attached.

And routing is a claim that the smaller model performs the task adequately, which needs an evaluation. What the profile alone establishes is that the *target* is well chosen.

## Connections

<!-- graph:begin -->
**Taught in:** [Caching, Batching, Routing](../curriculum/advanced/caching-batching-routing/index.md)

**Do not confuse with:** [Cache Key](cache-key.md)
<!-- graph:end -->
