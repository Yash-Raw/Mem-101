---
id: framework-memory-primitives
title: "Memory Primitives Inside Agent Frameworks"
kind: landscape
category: tool
volatility: high
last_verified: 2026-08-27
verified_by: "course maintainers"
claims_are_vendor_sourced: false
maps_to_concepts: [working-memory,context-assembly]
---

# Memory Primitives Inside Agent Frameworks

!!! warning "Dated snapshot — verified 2026-08-27"

**Representative:** LangMem and the checkpointing in LangGraph; the memory
classes historically shipped in LangChain.

## The architecture

Not standalone memory systems but memory *primitives* inside a broader agent
framework: conversation buffers, checkpointed graph state, and helpers for
storing and recalling facts.

## What it maps to in this course

Mostly [working memory](../../concepts/working-memory.md) and thread persistence.
Checkpointing solves "resume this conversation", which is a different problem
from "what do I know about this person" — the distinction the whole of
[context is not memory](../../curriculum/beginner/context-is-not-memory/index.md) is about.

## What to look at critically

Conversation-buffer style primitives are frequently mistaken for a memory layer.
They persist a transcript; they do not extract, reconcile, or forget. That is a
reasonable foundation and it is roughly where this course's Beginner level
starts, not where it ends. Check specifically whether anything in the framework
can mark a stored fact as no longer true.
