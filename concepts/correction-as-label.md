---
id: correction-as-label
title: "Correction as Label"
kind: concept
stage: extract
contrasts_with: [implicit-signal]
related: [supersession, consistency-window, memory-observability]
status: published
---

# Correction as Label

A user turn rejecting what the assistant just said: a negative example with a target attached.

## Why it matters in a memory layer

The pairing is what makes it a label. A correction with no assistant turn before it is the user changing their mind — an ordinary write, not evidence a belief was wrong.

Precision matters far more than recall, because the failure modes are not symmetric. A missed correction leaves a stale fact the next consolidation catches anyway; a **false** correction retires a belief that was true, citing the user's own words as the justification. Widen the pattern to any *"no"* and it fires on *"still no meat"* — a dietary fact the exam depends on.

And it can only ever arrive late. On this corpus it fixes eight of eleven wrong turns and cannot touch the three between the user announcing a change and complaining that you forgot it, because there is nothing to react to until the assistant is wrong out loud. A policy that corrects only when the user objects has made being wrong the trigger.

## Connections

<!-- graph:begin -->
**Taught in:** [Behaviour as Memory](../curriculum/advanced/implicit-signals/index.md)

**Do not confuse with:** [Implicit Signal](implicit-signal.md)
<!-- graph:end -->
