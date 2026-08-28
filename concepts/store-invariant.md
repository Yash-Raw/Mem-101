---
id: store-invariant
title: "Store Invariant"
kind: concept
stage: govern
contrasts_with: [leave-one-out]
related: [leak-assertion, memory-diff, bi-temporal-modeling]
status: published
---

# Store Invariant

Something that must always be true of the store, checked continuously rather than at deploy time.

## Why it matters in a memory layer

An index has few invariants worth asserting because it is **derived** — if it disagrees with the corpus, rebuild it, and drift is an operational nuisance. A memory store *is* the truth, so a violated invariant is not a stale derivation; it is data that is now wrong and will stay wrong.

Label them by **kind**, not severity. *Structural* means only a bug produces this — a cross-tenant memory visible, a belief retired before it was recorded, a dangling reference. *Policy* means unusual data produces this — a slot with more live beliefs than expected. Reported together unlabelled, a real bug and a heavy user look identical.

And test the checker. Running this course's seven against an earlier profile produces exactly one failure with a known cause — the belief retired nine months before it was recorded — which is the cheapest way to find out the invariants work at all.

## Connections

<!-- graph:begin -->
**Taught in:** [Invariants and Drift Detection](../curriculum/advanced/invariants-and-drift-detection/index.md)

**Do not confuse with:** [Leave-One-Out](leave-one-out.md)
<!-- graph:end -->
