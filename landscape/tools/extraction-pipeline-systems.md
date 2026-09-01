---
id: extraction-pipeline-systems
title: "Extraction-Pipeline Memory Systems"
kind: landscape
category: tool
volatility: high
last_verified: 2026-09-01
verified_by: "course maintainers"
claims_are_vendor_sourced: true
maps_to_concepts: [extraction,write-path,belief-updating]
---

# Extraction-Pipeline Memory Systems

!!! warning "Dated snapshot — verified 2026-09-01"
    Names and APIs here change on a scale of weeks. The mechanism is in
    [naive extraction](../../curriculum/beginner/naive-extraction/index.md); this page
    is only about who ships what.

**Representative system:** Mem0 (64,470 GitHub stars, counted 2026-09-01).
The two sibling pages name their systems without a number, which is the more
durable form — this one carried `~47K`, which was never right: the API said
64,470 the day it was written down.

## The architecture

The dominant commercial shape. A turn arrives, an LLM extracts candidate facts,
the candidates are compared against existing memories, and an LLM decides
between ADD / UPDATE / DELETE / NOOP. Storage is typically hybrid — vectors for
recall, a key-value layer for scoped lookup, and increasingly a graph layer for
relations.

## What it maps to in this course

This is `extract` → `resolve` → `store`, with the resolve step delegated to a
model. Everything in [conflict resolution](../../curriculum/intermediate/contradiction-detection/index.md)
is about that delegation.

## What to look at critically

The ADD/UPDATE/DELETE decision is usually a free-form LLM call, and that is the
single largest source of silent memory corruption in this architecture: an
unrelated new fact can trigger an UPDATE that overwrites a correct memory, with
no audit trail. When evaluating one of these systems, ask what happens to the
*previous* value — whether it is superseded or destroyed — and whether you can
reconstruct what the system believed last month. Many cannot.

Self-reported benchmark figures for systems in this category vary widely between
vendor publications and third-party comparisons. Treat any single number as
unverified until you have run it yourself.
