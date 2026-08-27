---
id: belief-updating
title: "Belief Updating"
kind: concept
stage: evolve
contrasts_with: [deduplication]
related: [supersession, memory-operations, slot, corroboration]
status: published
---

# Belief Updating

Changing what a system holds true when new evidence arrives: detecting that two
claims disagree, deciding which survives, and recording the change without
destroying what came before.

## Why it matters in a memory layer

It is the mechanism with no counterpart in retrieval, and the one every
characteristic memory bug traces back to. A corpus does not change its mind; a
memory layer does nothing else.

The division of labour is what makes it safe. *Detecting* that two beliefs
conflict is a language judgement, and a model does it well. *Deciding* which
wins is policy, and a model doing it produces different answers on different
runs with no record of why — which is how a correct belief gets silently
overwritten. Model detects, rules arbitrate.

The other discipline is that updating is not deleting. A retired belief keeps
its content and gains an `invalid_at`, so "what do I believe now" and "what did
I believe in March" are both answerable — see [supersession](supersession.md).
