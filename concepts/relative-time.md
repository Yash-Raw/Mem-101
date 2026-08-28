---
id: relative-time
title: "Relative Time Resolution"
kind: concept
stage: extract
contrasts_with: [event-time]
related: [bi-temporal-modeling, validity-interval, procedural-memory]
status: published
---

# Relative Time Resolution

Turning *"last week"*, *"since March"* and *"before the move"* into dates on the event axis — at write time, because the anchor does not survive.

## Why it matters in a memory layer

The phrase is the only statement of when a fact became true, and it is an offset from an instant the sentence does not contain. Once the turn leaves the context window the anchor is gone, so resolution happens on the write path or not at all.

The classes are not interchangeable. An offset is arithmetic — but *"last month"* names a calendar unit, and treating it as thirty days lands **nineteen days** from the truth. An event reference needs a lookup into the store and can legitimately fail. And some matches are not references at all: *"diff against last week"* is a step inside a taught procedure, and resolving it rewrites the recipe into a dated claim. A parser with no way to decline will always find something.

## Connections

<!-- graph:begin -->
**Taught in:** [Resolving 'Last Week'](../curriculum/advanced/relative-time-resolution/index.md)

**Do not confuse with:** [Event Time vs Ingestion Time](event-time.md)
<!-- graph:end -->
