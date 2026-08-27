---
id: locomo
title: "LoCoMo"
kind: landscape
category: benchmark
volatility: medium
last_verified: 2026-08-27
verified_by: "course maintainers"
claims_are_vendor_sourced: false
maps_to_concepts: [memory-staleness,retrieval-scoping]
---

# LoCoMo

!!! warning "Dated snapshot — verified 2026-08-27"

Long-term conversational memory. Built by a machine-human hybrid pipeline: two
LLM-driven personas hold multi-session dialogues grounded on persona profiles
and temporal event graphs. Conversations span up to ~32 sessions, ~600 turns,
~16K tokens on average. ~1,540 questions across single-hop, multi-hop,
open-domain and temporal categories.

## What it measures well

Multi-session recall over a realistic conversational shape — the same shape as
this course's canonical corpus, at larger scale.

## What it misses

**Knowledge updates and abstention.** LoCoMo does not systematically test what
happens when a fact *changes*, which is the failure this entire course is built
around. A system that never supersedes anything can score respectably here.
Do not read a LoCoMo number as evidence about staleness handling.

## Reading its numbers

Widely cited and widely re-run under different conditions — backing model,
retrieval budget, and which subset was used all move the result substantially.
Numbers are comparable only within a single report.
