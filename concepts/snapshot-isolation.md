---
id: snapshot-isolation
title: "Snapshot Isolation"
kind: concept
stage: evolve
contrasts_with: [lost-update]
related: [sleep-time-compute, provenance, deduplication]
status: published
---

# Snapshot Isolation

A job records **which ids** it read and is allowed an opinion about exactly those; everything else survives its write-back untouched.

## Why it matters in a memory layer

The recorded id set is the whole mechanism, because consolidation legitimately removes memories. A merged duplicate is absent from the output on purpose, and a memory that arrived after the read is absent because the job never saw it — the two are indistinguishable in the output alone. A write-back that infers intent from absence treats both as deletions, which is exactly how `replace` destroys data.

With the id set, the merge is not merely non-destructive but correct: racing a job against every fourth turn yields a store identical to the serialised run. It is also replayable, because scoped write-back plus an already-idempotent consolidation means a crashed job can simply be run again.

A lock would also work and would block the conversation for a full pass over the store — the cost that moving the work off the turn was meant to avoid.

## Connections

<!-- graph:begin -->
**Taught in:** [Background Job Mechanics](../curriculum/advanced/background-job-mechanics/index.md)

**Used in:** [Promotion as a Release](../curriculum/advanced/promotion-as-release/index.md)

**Do not confuse with:** [Lost Update](lost-update.md)
<!-- graph:end -->
