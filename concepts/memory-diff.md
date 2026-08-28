---
id: memory-diff
title: "Memory Diff"
kind: concept
stage: govern
contrasts_with: [memory-observability]
related: [supersession, lost-update, cascade-deletion]
status: published
---

# Memory Diff

What one write actually changed about the store: added, removed, retired.

## Why it matters in a memory layer

`removed` is the field to watch, and it should always be **zero**. Writes add and retire; nothing legitimate removes. So a non-zero value is either a deletion request or the lost update a background job produces when it writes back without a snapshot — two events that both deserve an alert and are otherwise silent.

Summed over every turn of this course's corpus, `removed` is 0. That zero is the assertion, which is why it is printed rather than filtered out: a number that is always zero costs nothing to report and is the only warning you will get on the day it is not.

`retired` is the other useful column — it locates the turns where a belief changed, which is where arbitration decisions live and where a differential diagnosis usually starts.

## Connections

<!-- graph:begin -->
**Taught in:** [Memory Observability](../curriculum/advanced/memory-observability/index.md)

**Do not confuse with:** [Memory Observability](memory-observability.md)
<!-- graph:end -->
