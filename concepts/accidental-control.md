---
id: accidental-control
title: "Accidental Control"
kind: concept
stage: govern
contrasts_with: [threat-model]
related: [write-authorisation, leak-assertion, memory-operations]
status: published
---

# Accidental Control

A security property that exists as a side effect of a mechanism built for another reason.

## Why it matters in a memory layer

On this course's system **all three** working defences are accidental. Arbitration was built to decide between two honest beliefs, the durability gate to keep requests out of the belief store, scope filtering because ranking across tenants returns noise. Each happens to block an attack, and none was designed to.

That matters because it predicts how they will be lost. `leak_check` is an assertion that always passes, and someone tidying dead code will delete it. The gate's imperative list will be narrowed by someone fixing a false positive. Both maintainers will be pursuing the purpose the mechanism was documented for, and neither will know it is load-bearing twice.

Naming the second purpose in the code is the cheapest available protection — and stating each control's **residual** matters as much, because a defence with an undocumented gap reads as complete.

## Connections

<!-- graph:begin -->
**Taught in:** [Memory Attacks](../curriculum/advanced/memory-attacks/index.md)

**Do not confuse with:** [Threat Model](threat-model.md)
<!-- graph:end -->
