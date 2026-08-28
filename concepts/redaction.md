---
id: redaction
title: "Redaction"
kind: concept
stage: govern
contrasts_with: [deletion]
related: [minimisation, personal-data, memory-record]
status: published
---

# Redaction

Rewriting a memory to carry less detail while still carrying the fact.

## Why it matters in a memory layer

Refusing personal data outright breaks the system — on this course's corpus it drops a diagnosis the exam requires. Redaction is the middle option, and it has to be designed **per kind**, because "less precise" is not one operation: a city is a useful address, there is no useful half of a phone number, and a health fact coarsens by dropping the *diagnosis event* while keeping the condition.

Some kinds have no middle. *"Sam is a nurse at St. Aubyn's"* stripped of its employer is still a named person's occupation, so it falls through to a token — keep that something was said, keep nothing of what.

And redaction changes the **id**, because ids are content-addressed. A redacted record is therefore a new record, which means the original must be explicitly retired: a policy that only adds the redacted form has doubled the data it meant to reduce.

## Connections

<!-- graph:begin -->
**Taught in:** [Redaction and Minimization](../curriculum/advanced/redaction-and-minimization/index.md)
<!-- graph:end -->
