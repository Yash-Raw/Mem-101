---
id: decay-function
title: "Decay"
kind: concept
stage: evolve
contrasts_with: []
related: [salience,reinforcement,relevance-vs-truth]
status: published
---

# Decay

Salience falling with age on a half-life, so that what has not been touched in a long time stops competing with what has.

## Why it matters in a memory layer

Decay is what keeps a bounded store honest, and its rate is the most consequential tuning decision in forgetting: too fast and the system loses the user, too slow and nothing is ever displaced. The rate is not one number, though -- it has to be scaled by memory type, because what decays is relevance rather than truth. A uniform half-life applied to this course's corpus emptied retrieval entirely inside seventeen months.

## Connections

<!-- graph:begin -->
**Taught in:** [Decay and Memory Tiers](../curriculum/intermediate/decay-and-tiers/index.md)

**Used in:** [Forgetting Under a Budget](../curriculum/intermediate/budgeted-forgetting/index.md)
<!-- graph:end -->
