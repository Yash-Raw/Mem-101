---
id: request-resolution
title: "Request Resolution"
kind: concept
stage: govern
contrasts_with: [cascade-deletion]
related: [label-not-permission, personal-data, provenance]
status: published
---

# Request Resolution

Working out which records a user's request actually names — before anything irreversible happens.

## Why it matters in a memory layer

The user's word for a thing is not the store's word for it. Asked to *"forget my old address"*, this course's store contains **zero** records matching *address*: it holds *"Priya lives at 47 Halloway Road, Bristol"*. The obvious implementation returns nothing and the request looks already satisfied.

Resolution therefore runs on the **labels** assigned at write time, which is the strongest argument for keeping classification as a durable label rather than a decision made and discarded — its most important consumer is a request that had not been made yet.

And *actionable* is not *unambiguous*. Here exactly one record is labelled `address`, and the request says **old** while that record is the address the user gave as new — the old one was never stored. A literal reading deletes nothing; a helpful reading deletes where they live. One candidate makes deletion mechanically possible and says nothing about intent, so the two are reported separately.

Search generously. A wide candidate set gets reviewed; a narrow one gets acted on, and deleting the wrong record is unrecoverable.

## Connections

<!-- graph:begin -->
**Taught in:** [Deletion That Actually Deletes](../curriculum/advanced/deletion-that-actually-deletes/index.md)

**Used in:** [Proving You Forgot](../curriculum/advanced/rtbf-and-auditability/index.md)

**Do not confuse with:** [Cascade Deletion](cascade-deletion.md)
<!-- graph:end -->
