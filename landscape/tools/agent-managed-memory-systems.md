---
id: agent-managed-memory-systems
title: "Agent-Managed Memory Systems"
kind: landscape
category: tool
volatility: high
last_verified: 2026-08-27
verified_by: "course maintainers"
claims_are_vendor_sourced: false
maps_to_concepts: [memory-promotion,working-memory,context-window]
---

# Agent-Managed Memory Systems

!!! warning "Dated snapshot — verified 2026-08-27"

**Representative system:** Letta, carrying the MemGPT lineage.

## The architecture

An operating-system analogy: the context window is RAM, an external store is
disk, and **the agent itself manages the boundary** through tool calls. The model
decides what to page in, what to write out, and what to edit — memory operations
are actions the agent takes, not a pipeline that runs around it.

## What it maps to in this course

The [promotion](../../curriculum/beginner/session-vs-longterm/index.md) decision,
handed to the model instead of a gate. Also the strongest contrast with the
system-managed approach every other architecture here takes.

## What to look at critically

The trade is control for autonomy. Agent-managed memory adapts to situations a
fixed pipeline handles badly, and it is correspondingly harder to audit, test,
and constrain — the same properties that make a promotion gate boring make it
verifiable. Ask how you would write a regression test for a memory decision the
model makes differently each run, and whether the system records *why* it wrote
what it wrote.
