---
id: hybrid-ranking
title: "Hybrid Ranking"
kind: concept
stage: retrieve
contrasts_with: [vector-search]
related: [score-fusion,salience,slot]
status: published
---

# Hybrid Ranking

Scoring a memory on several signals rather than one: what the question is about, how much of its vocabulary the memory contains, when the fact was true, how much it matters, whether its *type* answers this shape of question, whether it is about the right person, and whether it fills the attribute being asked about.

## Why it matters in a memory layer

Pure similarity answers "what looks like the question", which is the wrong question for a store that also knows when each fact was true, who it is about, and what attribute it fills. Every one of those signals was recorded by an earlier stage and consulted by none. On this course's corpus, adding them moves the correct answer from rank 20 to rank 2 — and the single most decisive one is slot membership, because it finds facts that share **no vocabulary at all** with the question asking about them.

## Connections

<!-- graph:begin -->
**Taught in:** [Hybrid Ranking](../curriculum/intermediate/hybrid-ranking/index.md)

**Used in:** [The Query Is Not the Last Message](../curriculum/intermediate/query-formulation/index.md)

**Do not confuse with:** [Vector Search](vector-search.md)
<!-- graph:end -->
