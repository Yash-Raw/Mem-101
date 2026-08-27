---
id: event-vs-state
title: "Events and States"
kind: concept
stage: extract
contrasts_with: []
related: [extraction,episodic-memory,semantic-memory]
status: published
---

# Events and States

Two ways to record the same change. An **event** says *what happened*: "started at Calico in January". A **state** says *what is now true*: "works at Calico Systems". A turn usually gives you the first; a question almost always wants the second.

## Why it matters in a memory layer

This is the single highest-cost extraction decision, because the two share almost no surface form and no ranking function bridges them. Record only the event and the fact becomes unreachable by the question it exists to answer — measurably so: in this course's corpus, extracting the job change as events alone leaves the correct answer ranked last of 36. States must be *derived* at write time; nothing downstream can invent one.

## Connections

<!-- graph:begin -->
**Taught in:** [Extraction Pipelines](../curriculum/intermediate/extraction-pipelines/index.md)

**Used in:** [Precision and Recall on the Write Path](../curriculum/intermediate/extraction-quality/index.md)
<!-- graph:end -->
