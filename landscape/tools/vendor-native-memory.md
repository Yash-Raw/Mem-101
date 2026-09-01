---
id: vendor-native-memory
title: "Vendor-Native Memory"
kind: landscape
category: tool
volatility: high
last_verified: 2026-09-01
verified_by: "course maintainers"
claims_are_vendor_sourced: true
maps_to_concepts: [write-path,belief-updating,retrieval-scoping,supersession]
---

# Vendor-Native Memory

!!! warning "Dated snapshot — verified 2026-09-01"
    Read from the vendors' own documentation on this date. Both are shipped
    products under active change; the mechanism they illustrate is in
    [belief updating](../../concepts/belief-updating.md).

The model providers now ship memory themselves, and the two largest ship
**opposite designs**. This is a distinct architecture class from the three
already catalogued here, and the choice between the two shapes is the single
biggest design decision anyone adopting vendor-native memory will make.

## Shape one: a directory of files you host

Anthropic's memory tool is a client-side file interface. The `tools` entry is
`{"type": "memory_20250818", "name": "memory"}`, available on Claude 4 and later
models, and it exposes six commands — `view`, `create`, `str_replace`, `insert`,
`delete`, `rename` — over a `/memories` path. The model *requests* file
operations; the application executes them against storage it controls. The
`/memories` prefix is mapped onto real storage by the implementer's handler.

There is no schema, no record type, no conflict detection and no ranking. The
memory is prose in files, and the model reads it back on demand.

## Shape two: a managed store that reconciles for you

Google's Memory Bank is the other pole: extraction and consolidation run as a
managed service. Its consolidation step compares newly extracted information
against what is already stored, and the documentation is explicit about both
the gate and the outcomes — *"Memory Bank checks that new memories are not
duplicative or contradictory before merging them with existing memories"*, and
*"Only memories with the same scope are considered for consolidation."*
Consolidation can mark an existing memory **CREATED**, **UPDATED** or
**DELETED**.

## What it maps to in this course

Memory Bank's pipeline is `extract` → `resolve`, run by a cloud vendor: the
exact concern of [contradiction detection](../../curriculum/intermediate/contradiction-detection/index.md)
and [memory operations](../../curriculum/intermediate/memory-operations/index.md).
Its scope dictionary is this course's `Scope` — the key every read filters on
before it ranks anything.

The file-shaped design maps to nothing in the `stores` module, which builds
vector, relational, graph and hybrid stores. A prose-in-files store is a fourth
option this course does not teach, and the honest reason is that it moves every
hard problem into the model's judgement at read time rather than solving it on
the write path.

## What to look at critically

**`DELETED` on contradiction is the disagreement.** This course argues that
belief updating never deletes: a superseded belief keeps its content and gains
an `invalid_at`, so *"what do I believe now"* and *"what did I believe in
March"* are both answerable — see
[supersession, not deletion](../../curriculum/intermediate/supersession-not-deletion/index.md).
A consolidation step that removes the losing memory answers only the first
question. Before adopting one, establish what is retained: whether a revision
history survives the delete, and whether you can reconstruct the store's belief
at a past date. That is the same question to ask of any system in the
[extraction-pipeline](extraction-pipeline-systems.md) category, and it is worth
asking harder of a managed one, because you cannot inspect the log yourself.

**A file store has no scope filter.** Multi-tenant correctness is entirely the
implementer's problem: nothing in a directory of prose enforces that one user's
memories cannot surface for another. The vendor documentation treats path
traversal as the security concern, which is a narrower question than tenancy.

**Neither shape gives you a decay story.** Both accumulate. One vendor's
guidance is to periodically delete files that have not been accessed recently,
which is recency as a proxy for importance — the substitution that
[salience scoring](../../curriculum/intermediate/salience-scoring/index.md)
measures and finds wanting.
