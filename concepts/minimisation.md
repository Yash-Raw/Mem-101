---
id: minimisation
title: "Minimisation"
kind: concept
stage: govern
contrasts_with: [personal-data]
related: [redaction, label-not-permission, element-cost]
status: published
---

# Minimisation

Storing less than you were told, on purpose, and measuring what less costs.

## Why it matters in a memory layer

You cannot minimise a corpus you did not write, so in retrieval this is a decision made once by whoever assembled the documents. A memory layer writes every record itself — the choice is available at **every write**, which is both the advantage and the trap: available so often that it is never made deliberately, and the default is to store the sentence as it arrived.

Measure it with the system's own task, not in characters removed. On this course's corpus, coarsening every kind of personal data costs nothing, and tokenising the contact details — destroying the street address and phone number outright — also costs nothing. Exactly one redaction breaks the answer: tokenising the health fact, because the exam needs the word *gluten*.

So the system that knows where the user lives is not more useful than the one that does not. That is an argument nobody can make without the measurement, and it is the whole reason to keep a `FULL` level to compare against.

## Connections

<!-- graph:begin -->
**Taught in:** [Redaction and Minimization](../curriculum/advanced/redaction-and-minimization/index.md)

**Do not confuse with:** [Personal Data](personal-data.md)
<!-- graph:end -->
