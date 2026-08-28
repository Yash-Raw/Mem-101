---
id: leak-assertion
title: "Leak Assertion"
kind: concept
stage: govern
contrasts_with: [write-authorisation]
related: [retrieval-scoping, memory-topology, invariant]
status: published
---

# Leak Assertion

A check that no memory visible to a reader belongs to a different user — always zero, and valuable entirely for the day it is not.

## Why it matters in a memory layer

It cannot catch a leak. `leak_check` reports memories *visible to this reader* **and** owned by someone else, and the visibility filter has already excluded those — the two conditions are contradictory unless the filter itself is broken. Write a foreign memory straight into the store and the count stays zero; break `Namespace.admits` and it returns one.

So it is an assertion about the filter rather than about the data, which is exactly what belongs in CI. Cross-tenant visibility is the one failure with no other signal: nothing errors, nothing logs, and the only symptom is a user seeing a fact about a stranger.

## Connections

<!-- graph:begin -->
**Taught in:** [Memory Access Control](../curriculum/advanced/memory-access-control/index.md)

**Do not confuse with:** [Write Authorisation](write-authorisation.md)
<!-- graph:end -->
