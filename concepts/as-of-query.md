---
id: as-of-query
title: "As-Of Query"
kind: concept
stage: retrieve
contrasts_with: [memory-staleness]
related: [bi-temporal-modeling, validity-interval, append-only-log]
status: published
---

# As-Of Query

A read that names its own point in time: what was true at a date, optionally as the store saw things at another date.

## Why it matters in a memory layer

Two different questions hide behind *"what did you know in June?"*. `as_of(when)` gives today's account of that day, corrections included. `as_of(when, believed_at_time=t)` gives the account the store would have given at `t`, mistakes and all. The second is what an audit asks for, and a system that only supports the first cannot show that it was ever wrong.

Without either, a question about the past is answered by whatever filter the read path already has. On this course's corpus that returns four facts about a job the user had not yet been offered — no layer misbehaving, every layer answering a different question correctly.

## Connections

<!-- graph:begin -->
**Taught in:** [Validity Intervals](../curriculum/advanced/validity-intervals/index.md)

**Used in:** [Three Temporal Questions](../curriculum/advanced/temporal-questions/index.md) · [Why Memory Eval Is Hard](../curriculum/advanced/why-memory-eval-is-hard/index.md)

**Do not confuse with:** [Staleness](memory-staleness.md)
<!-- graph:end -->
