---
id: implicit-signal
title: "Implicit Signal"
kind: concept
stage: extract
contrasts_with: [memory-record]
related: [correction-as-label, consistency-window, user-model]
status: published
---

# Implicit Signal

Evidence about a belief carried by how the user *reacts*, rather than by what they assert.

## Why it matters in a memory layer

Retrieval has implicit signals too — clicks, dwell, thumbs — and they are about documents: they tune which one to show, and the corpus is unaffected. Here the signal is about a **belief**, and the right response is not to rank it lower but to stop holding it. The user is reporting that the world changed and you missed it: a write-path event arriving through the read path.

Nothing in this course's store was listening. `access_count` is **0 on all 37 memories**, so no belief records ever having been used, let alone used and rejected.

It is also the cheapest signal available. Acting on the one correction in the corpus takes eleven wrong turns to three, at the cost of the policy that does nothing — because the user names the wrong belief out loud, and the assistant's own words identify it.

## Connections

<!-- graph:begin -->
**Taught in:** [Behaviour as Memory](../curriculum/advanced/implicit-signals/index.md)

**Do not confuse with:** [The Memory Record](memory-record.md)
<!-- graph:end -->
