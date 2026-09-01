---
id: memdelta
title: "MemDelta"
kind: landscape
category: benchmark
volatility: medium
last_verified: 2026-09-01
verified_by: "course maintainers"
claims_are_vendor_sourced: false
maps_to_concepts: [benchmark-claim,moving-ground-truth,absent-corpus]
---

# MemDelta

!!! warning "Dated snapshot — verified 2026-09-01"

*MemDelta: Controlled Baselines and Hidden Confounds in Agent Memory
Evaluation* — Kuan Wang, [arXiv:2606.29914](https://arxiv.org/abs/2606.29914),
submitted 2026-06-29.

Not a leaderboard. A **protocol** for comparing memory systems against
retrieval-augmented and full-context baselines with the confounds held still,
which is the thing every other benchmark on this page assumes someone else did.

## What it measures well

The confounds themselves. Its reported findings are all of the form *this
variable, which nobody controls for, moves the result more than the system
under test does*:

- swapping only the embedding model shifts accuracy by **±6.2pp**
- baseline strength varies substantially across model families, so a
  system compared against a weak backing model looks better than it is
- agent self-memory underperforms plain retrieval
- purpose-built memory systems show narrow rather than broad improvements,
  and cost more to run

Its recommendations are the reciprocal: standardise the embedding model,
stratify results by model family, and **report write-path cost**.

## What it misses

It is a measurement discipline, not a corpus. It will not tell you whether a
system handles supersession, scoping or deletion — it tells you whether the
number you are reading about any of those means anything. Pair it with a
benchmark that has ground truth for the behaviour you care about.

## Reading its numbers

This is the closest thing on this page to external backing for the
[wall this directory exists to enforce](../index.md). A single vendor figure,
quoted without its embedding model and backing model, is not a weak claim — by
MemDelta's own measurement it is a claim whose largest term is unstated.

Two of its findings converge with results this course reached independently and
by a different route: that **component metrics mislead before end-to-end ones
do**, which the eval module measures in
[component metrics](../../curriculum/advanced/component-metrics/index.md), and
that **write-path cost belongs in any honest report** — the figure this course
tracks as model calls per turn, and which its own read path drives to zero.
