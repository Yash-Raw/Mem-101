---
id: longmemeval
title: "LongMemEval"
kind: landscape
category: benchmark
volatility: medium
last_verified: 2026-08-27
verified_by: "course maintainers"
claims_are_vendor_sourced: false
maps_to_concepts: [belief-updating,memory-staleness]
---

# LongMemEval

!!! warning "Dated snapshot — verified 2026-08-27"

~500 questions across categories including multi-session recall, temporal
reasoning, and — the reason it matters here — **knowledge updates** and
**abstention**. A V2 exists, oriented toward longer-horizon "experienced
colleague" scenarios.

## What it measures well

The thing LoCoMo does not: whether a system notices that a fact was replaced,
and whether it declines to answer when it should not know. Its multi-session
split pushes into the regime where transcript replay stops working.

## What it misses

It is still a fixed corpus with fixed questions. It cannot measure write-path
cost, latency, or what a system does with input it was never designed for — and
it says nothing about deletion, privacy, or multi-agent behaviour.

## Reading its numbers

Reported scores for the same named system differ substantially between vendor
publications and independent comparisons. Where a figure matters to a decision,
re-run it on your own data.
