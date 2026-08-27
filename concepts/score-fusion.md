---
id: score-fusion
title: "Score Fusion"
kind: concept
stage: retrieve
contrasts_with: []
related: [hybrid-ranking,salience]
status: published
---

# Score Fusion

Combining several ranking signals into one number, and choosing what happens when they disagree — including how results from several sub-queries are merged into one context.

## Why it matters in a memory layer

The weights are where a ranker is right or wrong, and they cannot be reasoned out: on this corpus the type weight had to be swept before 0.5 was defensible, and merging strategy mattered as much as scoring. Global top-k lets the better-matching half of a compound question take every slot; strict round-robin hands the weaker half padding while a needed fact waits. Guaranteeing each sub-question its best answer and filling the rest by score is what finally put all four required facts in a five-slot context.

## Connections

<!-- graph:begin -->
**Taught in:** [Hybrid Ranking](../curriculum/intermediate/hybrid-ranking/index.md)
<!-- graph:end -->
