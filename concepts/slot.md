---
id: slot
title: "Slot"
kind: concept
stage: evolve
contrasts_with: [vector-search]
related: [belief-updating,type-rules]
status: published
---

# Slot

The attribute a claim fills — employer, diet, commute — as opposed to the words it uses. Two beliefs compete when they fill the same slot for the same subject.

## Why it matters in a memory layer

Slots are how conflict candidates are found, and the reason is measured rather than aesthetic: in this course's corpus the employer contradiction scores **0.285** on cosine similarity, below unrelated noise at 0.478 and far below a refinement at 0.669. Two claims can disagree completely while sharing almost no wording — *"data engineer at Northwind"* and *"works at Calico Systems"* overlap in one word. Any similarity threshold that catches that pair catches everything. Grouping by slot finds it directly, and shrinks the candidate set at the same time.

## Connections

<!-- graph:begin -->
**Taught in:** [Contradiction Detection](../curriculum/intermediate/contradiction-detection/index.md)

**Used in:** [ADD, UPDATE, MERGE, NOOP](../curriculum/intermediate/memory-operations/index.md)

**Do not confuse with:** [Vector Search](vector-search.md)
<!-- graph:end -->
