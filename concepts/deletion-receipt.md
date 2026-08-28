---
id: deletion-receipt
title: "Deletion Receipt"
kind: concept
stage: govern
contrasts_with: [cascade-deletion]
related: [proof-without-retention, memory-record, provenance]
status: published
---

# Deletion Receipt

A record that a deletion happened, holding everything except what was deleted.

## Why it matters in a memory layer

An index deletion is provable by rebuilding — the corpus legitimately still exists, and the absence is checkable against it. Here the record *was* the source, so the proof has to be constructed at the moment of deletion out of things that are not the data.

A receipt therefore carries the content-addressed **id**, the structures reached (zeroes included), when and on whose request, and the result of a re-scan. Not the content, and not the request's text either: storing what the user said in order to prove you honoured it is the same mistake one level down.

Two details do the work. `complete` is derived from a **re-scan**, not from the cascade's own counts — a cascade that missed a fourth copy reports success truthfully on its own terms, and only a re-scan describes what remains. And receipts **expire**, because a permanent record that a specific person asked to be forgotten is itself information about them.

## Connections

<!-- graph:begin -->
**Taught in:** [Proving You Forgot](../curriculum/advanced/rtbf-and-auditability/index.md)

**Do not confuse with:** [Cascade Deletion](cascade-deletion.md)
<!-- graph:end -->
