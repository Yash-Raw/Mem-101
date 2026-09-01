---
id: memory-interop
title: "Memory Portability and Interop"
kind: landscape
category: standard
volatility: high
last_verified: 2026-09-01
verified_by: "course maintainers"
claims_are_vendor_sourced: false
maps_to_concepts: [cascade-deletion,deletion-receipt,memory-lifecycle]
---

# Memory Portability and Interop

!!! warning "Dated snapshot — verified 2026-09-01"
    This page exists as much to **calibrate** an emerging effort as to record
    it. Read the caution before the contents.

Nothing in this course covers getting memories *out* of a system. Migration
within one store is taught in
[schema migration on live memory](../../curriculum/advanced/schema-migration-on-live-memory/index.md);
moving a user's accumulated memory between vendors is not, and as of this
snapshot there is no settled way to do it.

There is early work. It is worth knowing about and it is **not** a standard.

## The caution, first

A W3C **Community Group** is not a W3C standard: any group of people may
propose one, and a Community Group Report carries no W3C endorsement. The
[AI Agent Memory Interoperability Community Group](https://www.w3.org/community/ai-agent-memory-interop/)
was proposed 2026-05-18, issued its call for participation 2026-06-03, and
adopted a v1.0 charter 2026-06-19, with 22 listed participants.

Its charter normatively references an IETF Internet-Draft,
[draft-saihm-memory-protocol](https://datatracker.ietf.org/doc/draft-saihm-memory-protocol/)
— *The Sovereign AI Horizontal Memory (SAIHM) Protocol*. That draft is an
**Independent Submission**, and states of itself that it is not endorsed by the
IETF and has no formal standing in the IETF standards process. An Internet-Draft
is a submission, not a specification anyone has agreed to.

**And the three roles are one person.** The community group is chaired by
Russell Jackson; the Internet-Draft it normatively references is authored by
Russell Jackson; and he maintains SAIHM, an implementation in the same space.
That is not misconduct — early standards work often begins with one motivated
author — but a reader who sees "W3C" and "IETF" beside each other will infer
industry consensus, and there is not yet any. Weight it as one person's
proposal with a venue, and check the participant list before citing it as more.

## What is actually being proposed

Two artefacts, both readable in an afternoon:

- **SAIHM**, the protocol draft: post-quantum identity binding, per-cell
  encryption with wallet-derived keys, revocable sharing contracts, and
  cryptographic erasure aligned to GDPR Article 17. It is chain-agnostic in
  its own words while naming a specific blockchain as its reference deployment
  — worth knowing before adopting the model wholesale.
- **memorywire** ([arXiv:2606.01138](https://arxiv.org/abs/2606.01138),
  Thamilvendhan Munirathinam, v1 2026-05-31), a JSON-Schema wire format with
  five operations — `remember`, `recall`, `forget`, `merge`, `expire` — across
  four memory types.

## What it maps to in this course

**`forget` and `expire` as separate operations** is the distinction this course
spends a whole level on: deletion is a governance obligation, decay is a
relevance adjustment, and collapsing them loses both. Any portability format
that models only one of them cannot round-trip a memory layer built here.

**Cryptographic erasure** is one answer to the problem posed in
[deletion that actually deletes](../../curriculum/advanced/deletion-that-actually-deletes/index.md):
destroying a key is tractable where chasing every derived copy is not. The
course's finding stands against it as a caution — a deleted record's traces
survive in other records, and no key destruction reaches a timestamp that was
copied into a neighbour.

The reason to watch this space is not the specifications. It is that
portability is being *felt* as a problem, which is itself evidence that memory
is now something users accumulate and expect to keep.
