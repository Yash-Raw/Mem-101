---
id: salience
title: "Salience"
kind: concept
stage: evolve
contrasts_with: [vector-search, durability-gate]
related: [reinforcement, decay-function, eviction]
status: published
---

# Salience

How much a memory matters, as a score that moves. Not how well it matches a
query — that is relevance, it is a property of the *question*, and it is
computed fresh every time.

## Why it matters in a memory layer

Without it every memory is equally important, so nothing can be ranked down and
nothing can be aged out: the store only grows and every query pays for the whole
history. Salience is what makes forgetting possible at all.

It is also the signal most often misapplied. Salience is *importance*, and
adding it to a relevance score does not produce a better ranking — measured on
this course's corpus, weighting a plain cosine ranker by salience moves the
correct answer **down**, from rank 20 to 22, and promotes a taught procedure to
first place for a question about diet. The procedure genuinely is one of the
most important things in the store. It is not what was asked.

Distinct from the [durability gate](durability-gate.md), which is a boolean
decision made once at write time with no usage history. Salience accumulates
evidence — explicit instruction, corroboration, and use — and keeps moving.
