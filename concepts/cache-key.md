---
id: cache-key
title: "Cache Key"
kind: concept
stage: govern
contrasts_with: [model-routing]
related: [vector-index, cost-profile, memory-record]
status: published
---

# Cache Key

What a cached result is looked up by — and the reason a completion cache is worthless on a memory layer's write path.

## Why it matters in a memory layer

Retrieval caches at the read path, where queries follow a popularity distribution and the same question really is asked repeatedly. A memory layer's expensive path is **writes**, and a write is one person saying something they have not said before: on this course's corpus, 24 turns produce **24 distinct keys and zero hits**. No key design fixes that; it is what a conversation is.

The cacheable thing is not the call, it is the **embedding of a stored memory**, which recurs because the memory persists. Keyed on the content-addressed id, a warm read costs 2 embeddings and a cold one costs 20.

That cache was built two levels earlier to stop re-embedding the corpus per query — a scaling concern, not a cost one. Claiming it as a cost optimisation would misattribute work done for a different reason, which is worth resisting because it is the only cache here that works.

## Connections

<!-- graph:begin -->
**Taught in:** [Caching, Batching, Routing](../curriculum/advanced/caching-batching-routing/index.md)

**Do not confuse with:** [Model Routing](model-routing.md)
<!-- graph:end -->
