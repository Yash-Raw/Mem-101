---
id: temporal-routing
title: "Temporal Routing"
kind: concept
stage: retrieve
contrasts_with: [retrieval-scoping]
related: [as-of-query, validity-interval, recency-bias]
status: published
---

# Temporal Routing

Deciding, before retrieval, which temporal question is being asked — what is true now, what was true then, or when it changed — and releasing the filters that assume the first.

## Why it matters in a memory layer

A date in a question is not a matching term. *"Priya is a data engineer at Northwind Labs"* contains no year, so no amount of tuning the similarity function surfaces it for a question about 2025; the information the question needs lives in the validity interval, not the string. On this course's corpus the read path finds **0 of 4** such memories in its top five.

Routing alone is not enough either. A read path accumulates assumptions that the question is about the present — a belief-time filter, and a tier cap whose decay is measured from now. Releasing one gets **1 of 4**; releasing both gets **4 of 4**. The property that made a memory droppable is often exactly the property that makes it the answer.

## Connections

<!-- graph:begin -->
**Taught in:** [Three Temporal Questions](../curriculum/advanced/temporal-questions/index.md)

**Do not confuse with:** [Retrieval Scoping](retrieval-scoping.md)
<!-- graph:end -->
