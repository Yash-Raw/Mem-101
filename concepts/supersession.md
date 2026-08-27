---
id: supersession
title: "Supersession"
kind: concept
stage: evolve
contrasts_with: []
related: [belief-updating,memory-record,event-time]
status: published
---

# Supersession

Retiring a belief by marking when it stopped being true (`invalid_at`) and what replaced it (`superseded_by`), rather than removing it.

## Why it matters in a memory layer

It costs one nullable timestamp and buys every historical question: *where do I work* and *where did I work before* both stay answerable, and any belief the system once held can be explained. Deletion answers the first and destroys the rest permanently. The date matters too — a belief is invalid from the moment its replacement became true, which is **event time**, not when the system found out. Genuine erasure is a different operation for a different reason, and it is a governance obligation rather than an update.

## Connections

<!-- graph:begin -->
**Taught in:** [Supersede, Never Destroy](../curriculum/intermediate/supersession-not-deletion/index.md)
<!-- graph:end -->
