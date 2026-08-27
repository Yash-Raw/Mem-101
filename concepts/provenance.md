---
id: provenance
title: "Provenance"
kind: concept
stage: govern
contrasts_with: [namespace]
related: [memory-record, belief-updating, entity-resolution]
status: published
---

# Provenance

Where a memory came from and how much to believe it: the turn or agent that
produced it (`source_id`), who actually asserted it (`speaker`), and the weight
that assertion carries (`authority`).

## Why it matters in a memory layer

Three separate jobs, and collapsing any two of them loses something you cannot
reconstruct later.

`source_id` is what makes deletion possible at all — a memory written without
one cannot be removed on request, because nothing identifies what to remove, and
neither can a derived summary be traced back to the episode it consumed.

`speaker` and `authority` are what stop hearsay becoming fact. "My colleague
thinks she's moving to Berlin" and "I'm moving to Berlin" produce the same
sentence after extraction; only provenance distinguishes them. Flatten the
distinction and a third party's guess silently becomes a first-party belief that
will outrank the truth.

Distinct from [namespace](namespace.md): namespace answers *where is this filed
and who may read it*, provenance answers *who said it and do we believe them*. A
memory can be perfectly visible and correctly disbelieved.
