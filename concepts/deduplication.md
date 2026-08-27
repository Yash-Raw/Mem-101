---
id: deduplication
title: "Deduplication"
kind: concept
stage: evolve
contrasts_with: [entity-resolution, idempotency]
related: [derived-memory, memory-record]
status: published
---

# Deduplication

Collapsing records that say the same thing. Not records that are *about* the
same thing — that is [entity resolution](entity-resolution.md) — and not the
same turn processed twice, which is [idempotency](idempotency.md).

## Why it matters in a memory layer

The three are easy to conflate and fail differently. Idempotency is settled at
write time by a content-addressed id and catches re-ingestion of one turn.
Deduplication catches the same *fact* arriving from different turns, where the
sources differ, the ids differ, and idempotency is blind by construction.

The cost of the two mistakes is not symmetric. A missed duplicate wastes a slot
in the token budget. A wrong merge destroys a distinction — and the tempting
near-misses are refinements and contradictions, which score high precisely
because they are about the same subject. So the threshold belongs near
certainty, and everything below it is a *relationship* for conflict detection
to name rather than a repetition to collapse.
