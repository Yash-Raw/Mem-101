---
id: label-not-permission
title: "Label, Not Permission"
kind: concept
stage: govern
contrasts_with: [write-authorisation]
related: [personal-data, redaction, deletion]
status: published
---

# Label, Not Permission

Classifying a memory as sensitive without deciding, at that moment, what may be done with it.

## Why it matters in a memory layer

The same fact is required in one context and unacceptable in another. A dietary restriction must reach a question about food and must not reach a travel agent — two decisions, made by two stages, from one label. Collapse them at the write gate and the strictest one wins everywhere, which on this course's corpus means the exam fails.

So classification produces a label that redaction, access control and deletion each consult. Deletion in particular *needs* it: a cascade cannot find what was never named.

Use patterns rather than a classifier on this path. A false negative is a missed label; a false positive is a fact the user volunteered and the system refuses to remember. Both are visible in a diff, and neither justifies a nondeterministic decision about what to keep.

## Connections

<!-- graph:begin -->
**Taught in:** [PII on the Write Path](../curriculum/advanced/pii-on-the-write-path/index.md)

**Do not confuse with:** [Write Authorisation](write-authorisation.md)
<!-- graph:end -->
