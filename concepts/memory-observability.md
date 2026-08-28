---
id: memory-observability
title: "Memory Observability"
kind: concept
stage: govern
contrasts_with: [disclosure]
related: [provenance, supersession, memory-diff]
status: published
---

# Memory Observability

Answering *"why do you believe this about me?"* — a question a user asks, about a claim the system made in the first person.

## Why it matters in a memory layer

*"Why did you return this document?"* is answered by a score, and the document is unchanged by having been returned. Here the answer must be a **provenance chain**, it is asked by users and regulators rather than engineers, and it must still work years later about a belief that has since been retired.

Most of it needs no logging. The source turn, the speaker and their authority, both validity spans, and the supersession chain are fields the record already carries — and the chain is walkable only because **nothing on it was destroyed**, which is the audit argument for retiring rather than deleting, finally cashed.

It also surfaces things nobody would look for. On this course's store, a retired employer belief was replaced by *"Priya is a staff engineer"* rather than by *"Priya works at Calico Systems"* — correct, and undiscoverable by reasoning about the code.

## Connections

<!-- graph:begin -->
**Taught in:** [Memory Observability](../curriculum/advanced/memory-observability/index.md)

**Do not confuse with:** [Disclosure](disclosure.md)
<!-- graph:end -->
