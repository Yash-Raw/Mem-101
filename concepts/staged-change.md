---
id: staged-change
title: "Staged Change"
kind: concept
stage: evolve
contrasts_with: [snapshot-isolation]
related: [rollback, reflection, supersession]
status: published
---

# Staged Change

A consolidation computed against a known base and measured before it is applied — what would change, whether the system is better, and against which store it is valid.

## Why it matters in a memory layer

Consolidation writes into the source of truth, so "try it and see" costs the thing you were trying to protect. Staging separates the questions a job that writes directly answers all at once and reports on none of.

Two details carry the weight. The retirement set is read off `derived_from` rather than specified separately, so the change and its provenance cannot drift apart. And the preview must run **every** step the application runs: on this course's corpus, omitting the scoring pass from the preview alone is the difference between a change that costs five tokens of headroom and one where the exam never passes at any budget — the derived beliefs land unscored and invisible while their eight sources have already been retired.

The fix is structural rather than careful: promotion calls the preview.

## Connections

<!-- graph:begin -->
**Taught in:** [Promotion as a Release](../curriculum/advanced/promotion-as-release/index.md)

**Do not confuse with:** [Snapshot Isolation](snapshot-isolation.md)
<!-- graph:end -->
