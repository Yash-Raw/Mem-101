---
id: corroboration
title: "Corroboration"
kind: concept
stage: evolve
contrasts_with: [deduplication]
related: [belief-updating,provenance]
status: published
---

# Corroboration

Independent sources asserting the same thing, and the raised confidence that should follow.

## Why it matters in a memory layer

The appealing shortcut is to treat textual similarity as evidence of agreement, and it does not survive measurement: on this corpus a refinement scores 0.669, a genuine corroboration 0.505, and a flat contradiction 0.439. No threshold separates them, so a similarity-driven confidence boost grows most certain about the facts it should be doubting. Corroboration is only safe once something has *named* the relationship — which makes it downstream of conflict detection, not a substitute for it.

## Connections

<!-- graph:begin -->
**Taught in:** [From Episode to Belief](../curriculum/intermediate/episodic-to-semantic/index.md)

**Used in:** [Contradiction Detection](../curriculum/intermediate/contradiction-detection/index.md) · [Salience Scoring](../curriculum/intermediate/salience-scoring/index.md)

**Do not confuse with:** [Deduplication](deduplication.md)
<!-- graph:end -->
