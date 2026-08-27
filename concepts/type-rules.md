---
id: type-rules
title: "Type Rules"
kind: concept
stage: store
contrasts_with: [memory-record]
related: [semantic-memory,episodic-memory,belief-updating]
status: published
---

# Type Rules

The behaviour a memory's type governs: whether it can be contradicted, whether it expires on its own, what a correct update does to it, and the query shape that should surface it.

## Why it matters in a memory layer

Type is where a memory's whole life is decided, and the load-bearing entry is `can_contradict`. Only a claim about *now* can be made false by another claim about now, so almost every mechanism at this level — conflict detection, arbitration, supersession — applies to exactly one of the four types. Getting this wrong routes preferences into a type that never expires, and they then outlive the person's actual preferences.

## Connections

<!-- graph:begin -->
**Taught in:** [The Typed Memory Model](../curriculum/intermediate/typed-memory-model/index.md)

**Used in:** [Contradiction Detection](../curriculum/intermediate/contradiction-detection/index.md) · [Extraction Pipelines](../curriculum/intermediate/extraction-pipelines/index.md) · [ADD, UPDATE, MERGE, NOOP](../curriculum/intermediate/memory-operations/index.md)

**Do not confuse with:** [The Memory Record](memory-record.md)
<!-- graph:end -->
