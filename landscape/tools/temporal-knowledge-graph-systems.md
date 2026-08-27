---
id: temporal-knowledge-graph-systems
title: "Temporal Knowledge-Graph Memory Systems"
kind: landscape
category: tool
volatility: high
last_verified: 2026-08-27
verified_by: "course maintainers"
claims_are_vendor_sourced: false
maps_to_concepts: [bi-temporal-modeling,entity-resolution,event-time]
---

# Temporal Knowledge-Graph Memory Systems

!!! warning "Dated snapshot — verified 2026-08-27"

**Representative systems:** Graphiti (open source), and Zep, which wraps it.

## The architecture

Facts become edges in a graph, and every edge carries validity: when the fact
became true, and when it stopped. A new fact that contradicts an old one does
not overwrite it — it closes the old edge's validity interval. Queries can be
asked "as of" a point in time.

## What it maps to in this course

Directly onto [bi-temporal modeling](../../curriculum/advanced/validity-intervals/index.md)
and [supersession](../../curriculum/intermediate/supersession-not-deletion/index.md).
If you build the Level 2 capstone as taught, you will have built a simplified
version of this shape.

## What to look at critically

This architecture's advantage is real and specific: it is the only common shape
that answers "what did I believe then". The costs are also real — graph
construction is expensive on the write path, entity resolution becomes
load-bearing rather than optional, and a wrong merge corrupts a whole
neighbourhood rather than one record.

Published comparisons show a substantial gap in favour of this architecture on
temporal-reasoning benchmark categories specifically. That is the category where
the design should win, so it is weak evidence of general superiority.
