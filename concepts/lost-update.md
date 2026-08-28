---
id: lost-update
title: "Lost Update"
kind: concept
stage: evolve
contrasts_with: [snapshot-isolation]
related: [sleep-time-compute, consistency-window, deduplication]
status: published
---

# Lost Update

A background job reads the store, computes, and writes back — destroying anything that arrived in between.

## Why it matters in a memory layer

Consolidation writes back into the store it read. The output is not a cache of the input, it replaces it: duplicates are merged away, losers retired, confidences moved. So there is no authoritative copy to re-derive from, and a write lost here is lost for good — unlike an index, which can always be rebuilt from a corpus that never changed.

On this course's corpus, `store.replace(consolidate(store.all()))` destroys **33 memories** summed over every position a one-turn job could occupy. The worst single turn takes all four memories announcing the job change: the job that exists to keep the store correct deletes the correction. Scheduling consolidation more often — the fix from the previous lesson — multiplies the exposure rather than reducing it.

Nothing errors, and the store ends with exactly the number of memories the job expected.

## Connections

<!-- graph:begin -->
**Taught in:** [Background Job Mechanics](../curriculum/advanced/background-job-mechanics/index.md)

**Do not confuse with:** [Snapshot Isolation](snapshot-isolation.md)
<!-- graph:end -->
