---
id: open-item
title: "Open Item"
kind: concept
stage: govern
contrasts_with: [release-report]
related: [failure-class, differential-diagnosis, saturated-metric]
status: published
---

# Open Item

A known defect, measured and attributed, published alongside what works.

## Why it matters in a memory layer

**A release report with no open items is a release report nobody checked.** An empty list means either that nobody looked closely or that the looking stopped being reported, and the second is worse: the gaps still exist and are now undocumented.

Each item needs a **number** and a **lesson**. The number is what distinguishes a defect from a worry — nine unnameable memories, four records carrying a deleted timestamp, 104× candidate pairs. The lesson is where the measurement and its reproduction live, which is what someone picking the item up in six months actually needs; a ticket says what to do and not how the problem was found.

Collecting them also reveals overlap invisible from inside any one lesson. Two of this course's six trace to the same stage, which from either lesson looks like a local problem.

## Connections

<!-- graph:begin -->
**Taught in:** [Hardening Pass](../curriculum/advanced/capstone-finale/index.md)

**Do not confuse with:** [Release Report](release-report.md)
<!-- graph:end -->
