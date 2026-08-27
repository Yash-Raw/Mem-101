---
id: entity-resolution
title: "Entity Resolution"
kind: concept
stage: store
contrasts_with: [deduplication]
related: [canonical-entity, coreference, entity-fragmentation]
status: published
---

# Entity Resolution

Deciding which surface forms denote the same real thing, and linking them to one
canonical identity. "Sam", "Samira", "Sammy", "my partner" and a bare "She" are
five ways of referring to one person; resolution is what makes them one node.

## Why it matters in a memory layer

Without it, evidence about a person is split across records that never meet, so
nothing accumulates and no contradiction between them is detectable — the system
holds four half-pictures and cannot tell they are the same picture. It is
invisible in testing, because every individual record looks correct.

Distinct from [deduplication](deduplication.md): dedupe asks whether two
*memories* say the same thing, resolution asks whether two *mentions* point at
the same thing. Two memories about one person are usually both worth keeping.

The property that makes it tractable is that resolution **links rather than
rewrites** — the canonical id goes in a separate field and the content stays
exactly as spoken, so provenance survives and the operation can be re-run or
undone.
