---
id: write-authorisation
title: "Write Authorisation"
kind: concept
stage: govern
contrasts_with: [retrieval-scoping]
related: [competence, memory-topology, provenance]
status: published
---

# Write Authorisation

Deciding what a writer may put into the store — attribution, tenant, and clock — before anything is stored.

## Why it matters in a memory layer

Retrieval access control is enforced at read time because that is the only time it matters: a document nobody may read is harmless in the index. A memory a writer should not have written is **not harmless in the store**. It participates in consolidation, arbitration, decay and the store's own clock before any reader appears.

Three refusals cover it. **Wrong user** crosses a tenant boundary. **Impersonation** stays inside the right tenant and is wrong only about attribution — an agent filing under the bare user scope, so the claim reads as something the user said. And **future dated**, which is the one that does not look like access control: the store ages memories relative to its newest event, so a single record dated ahead drops the retrievable set from **18 to 5** without its claim ever being believed.

Return the refusals rather than logging and dropping them. A write path that silently discards is indistinguishable from one that received nothing.

## Connections

<!-- graph:begin -->
**Taught in:** [Memory Access Control](../curriculum/advanced/memory-access-control/index.md)

**Used in:** [Memory Attacks](../curriculum/advanced/memory-attacks/index.md) · [PII on the Write Path](../curriculum/advanced/pii-on-the-write-path/index.md)

**Do not confuse with:** [Retrieval Scoping](retrieval-scoping.md)
<!-- graph:end -->
