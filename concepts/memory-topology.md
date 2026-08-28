---
id: memory-topology
title: "Memory Topology"
kind: concept
stage: store
contrasts_with: [retrieval-scoping]
related: [provenance, namespace, access-control]
status: published
---

# Memory Topology

How namespaces are arranged when more than one agent writes about the same person: private, shared, hierarchical, or blackboard.

## Why it matters in a memory layer

The boundary runs *inside* a tenant. Several writers of differing trust contribute facts about one user, into a store that user also reads — a shape a retrieval index has no place for, since a document does not belong to one participant in a conversation.

Most stores arrive at a topology without choosing it. This course's falls out of where the write path files agent rows: three namespaces, the user's own plus one per agent, which is hierarchical. Priced by what each reader loses, the surprise is that **for the user, hierarchical and shared are identical** — the isolation is entirely between agents — and that hierarchical leaks **exactly the PII shared leaks**, two memories, to the least-trusted writer.

The shape that leaks nothing leaves an agent able to read one memory: its own. Isolation that removes the shared subject is just several small stores, so the mechanism that separates a user from their agents is not a topology at all.

## Connections

<!-- graph:begin -->
**Taught in:** [Memory Topologies](../curriculum/advanced/memory-topologies/index.md)

**Used in:** [Provenance and Trust](../curriculum/advanced/provenance-and-trust/index.md)

**Do not confuse with:** [Retrieval Scoping](retrieval-scoping.md)
<!-- graph:end -->
