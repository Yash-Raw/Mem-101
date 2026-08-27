---
id: atomic-fact
title: "Atomicity"
kind: concept
stage: extract
contrasts_with: []
related: [extraction,memory-record]
status: published
---

# Atomicity

One fact per record, written so it stands alone without its originating turn. "Priya does not eat meat" rather than "she said she'd gone vegetarian but now eats fish sometimes".

## Why it matters in a memory layer

Atomicity is what makes a memory *updatable*. You cannot mark half a sentence superseded, so a compound memory has to be deleted and rewritten wholesale, losing its history. Getting the grain right at write time is what makes belief updating possible at all.

## Connections

<!-- graph:begin -->
**Taught in:** [Naive Extraction](../curriculum/beginner/naive-extraction/index.md)

**Used in:** [Atomic Memories](../curriculum/intermediate/atomic-memories/index.md) · [Extraction Pipelines](../curriculum/intermediate/extraction-pipelines/index.md)
<!-- graph:end -->
