---
id: beam
title: "BEAM"
kind: landscape
category: benchmark
volatility: medium
last_verified: 2026-08-27
verified_by: "course maintainers"
claims_are_vendor_sourced: false
maps_to_concepts: [context-window,token-budget]
---

# BEAM

!!! warning "Dated snapshot — verified 2026-08-27"

Introduced in *Beyond a Million Tokens: Benchmarking and Enhancing Long-Term
Memory in LLMs* (ICLR 2026). 100 conversations, each up to **10 million tokens**,
with ~2,000 probing questions, generated through a planning pipeline producing
narratives, user profiles and timelines.

## What it measures well

Behaviour far past the point where any context window is a viable strategy —
which makes it the most direct empirical answer to "just use a bigger window".
It reports token consumption and latency alongside accuracy, so cost is visible
rather than assumed.

## What it misses

Synthetic conversations have synthetic contradiction patterns. Real users change
their minds in messier, sparser ways than a generation pipeline produces, and
the hard cases in practice tend to be the ambiguous ones a planner would not think
to author.

## Reading its numbers

New enough at this snapshot that independent replications are limited. Treat the
scale claim as the durable contribution and individual system rankings as provisional.
