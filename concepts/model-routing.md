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

The profile points at two targets, and they split the write path evenly: extraction, synchronous, and conflict **detection**, entirely deferred. Both are bounded tasks — a schema on one side, four labels on the other — which is the shape small models suit.

Check first which stages call a model at all. *Arbitration* looks like an obvious candidate and makes **none** — `deterministic-freshness` made it rules, because its output changes what is believed and has to be explainable. Conflict *detection* is one word away and is a model call. Routing a stage that calls nothing is a config change with no effect and a plausible story attached, and confusing the two is how a cost review reports one target where there are two.

And routing is a claim that the smaller model performs the task adequately, which needs an evaluation. What the profile alone establishes is that the *target* is well chosen.

## Connections

<!-- graph:begin -->
**Taught in:** [Caching, Batching, Routing](../curriculum/advanced/caching-batching-routing/index.md)

**Do not confuse with:** [Cache Key](cache-key.md)
<!-- graph:end -->
