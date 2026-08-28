---
id: release-report
title: "Release Report"
kind: concept
stage: govern
contrasts_with: [benchmark-claim]
related: [open-item, cost-profile, store-invariant]
status: published
---

# Release Report

What a memory system actually does, what it costs, and what it still gets wrong — assembled from measurements rather than summarised.

## Why it matters in a memory layer

A retrieval system ships against a benchmark: a score on a shared corpus, comparable to somebody else's. It is a weak claim and it is **legible**, and there is industry-wide agreement about what it means.

There is no such agreement here — memory benchmarks share neither their corpora nor their division of labour with the reading model. So the honest artifact is not a number. It is the measurements **plus the gaps**, each naming the lesson that found it, so a reader can reproduce any claim and see the shape of what was not attempted.

Three exams answer different questions and all three are needed: does the store believe the right thing, would it ever say it, and does it survive a tight context. A system can pass the first and fail the second, which is a test in this course's suite for exactly that reason.

## Connections

<!-- graph:begin -->
**Taught in:** [Hardening Pass](../curriculum/advanced/capstone-finale/index.md)

**Do not confuse with:** [Benchmark Claim](benchmark-claim.md)
<!-- graph:end -->
