---
id: backfill
title: "Backfill"
kind: concept
stage: store
contrasts_with: [shape-change]
related: [relative-time, snapshot-isolation, staged-change]
status: published
---

# Backfill

Reprocessing history through a stage the records predate.

## Why it matters in a memory layer

It should be **optional**, which requires the new field to have an honest fallback. On this course old records answer as-of queries with `happened_at` — *when this was asserted* rather than *when it was true* — so a store that never backfills is imprecise rather than broken, and the migration is one phase instead of two.

It should be **restartable**, and the cheapest way is determinism rather than checkpoints: the parser derives its value from the record's own content, so a second pass computes the same answer and changes nothing. The same property consolidation needed to be safely re-run after a crash.

And its value is not coverage. This one updates **4 of 37** records — precisely the relative-time phrases whose event time differs from the instant they were said. The other 33 were already answering correctly.

## Connections

<!-- graph:begin -->
**Taught in:** [Migrating Live Memory](../curriculum/advanced/schema-migration-on-live-memory/index.md)

**Do not confuse with:** [Shape Change](shape-change.md)
<!-- graph:end -->
