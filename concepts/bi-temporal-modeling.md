---
id: bi-temporal-modeling
title: "Bi-Temporal Modeling"
kind: concept
stage: store
contrasts_with: [event-time]
related: [memory-record, supersession, validity-interval]
status: published
---

# Bi-Temporal Modeling

Two independent time axes on one record: when a fact was **true** (`valid_from` … `valid_to`) and when the system **believed** it (`recorded_at` … `invalid_at`). Four instants, not two.

## Why it matters in a memory layer

The axes move independently, and the cases where they disagree are the ones an audit asks about. A fact stops being true while nobody is watching — `valid_to` in the past, `invalid_at` still unset. A belief is retired in error — `invalid_at` set, the thing still true. Under a single time field neither is describable, and *"when did you stop believing this, and were you right to?"* has no answer.

Having the fields is not the same as populating them. Audited on this course's corpus, **37 of 37 memories carry an event time that is simply the instant the record was written**, and **none** records that anything ended. A field that is always a copy of another field is schema, not information.

## Connections

<!-- graph:begin -->
**Taught in:** [Two Clocks](../curriculum/advanced/two-clocks/index.md)

**Used in:** [Resolving 'Last Week'](../curriculum/advanced/relative-time-resolution/index.md) · [Validity Intervals](../curriculum/advanced/validity-intervals/index.md)

**Do not confuse with:** [Event Time vs Ingestion Time](event-time.md)
<!-- graph:end -->
