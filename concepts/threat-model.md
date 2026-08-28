---
id: threat-model
title: "Threat Model"
kind: concept
stage: govern
contrasts_with: [accidental-control]
related: [write-authorisation, competence, cascade-deletion]
status: published
---

# Threat Model

The four ways a memory layer is attacked — poisoning, injection, cross-user reads, extraction — written down so the defences can be checked against something.

## Why it matters in a memory layer

A retrieval corpus is written by people who are not attacking you and curated before it is indexed. A memory layer's corpus is written **by the adversary**, one turn at a time, and every record is a first-person claim about the person whose questions it will answer. There is no curation step to defend, and the standard mitigation — treat retrieved text as data, not instructions — is unavailable, because believing it is the function.

On this course's system three of the four are covered and the fourth, extraction, is not. Deleting the address leaves **four** records carrying its exact timestamp, with **zero** `derived_from` edges for a cascade to follow: what survives is not the street name but the event, which is arguably what the deletion was about.

The value of writing the four down is that `extraction: False` becomes a fact in the codebase rather than an absence nobody recorded.

## Connections

<!-- graph:begin -->
**Taught in:** [Memory Attacks](../curriculum/advanced/memory-attacks/index.md)

**Do not confuse with:** [Accidental Control](accidental-control.md)
<!-- graph:end -->
