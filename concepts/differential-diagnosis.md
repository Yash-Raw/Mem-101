---
id: differential-diagnosis
title: "Differential Diagnosis"
kind: concept
stage: govern
contrasts_with: [failure-class]
related: [failure-class, eval-suite, memory-observability]
status: published
---

# Differential Diagnosis

The measurement that separates two causes of the same symptom — the column a field guide is actually for.

## Why it matters in a memory layer

Listing causes is easy and nearly useless when a symptom has three of them. What resolves a case is a cheap check that discriminates: replay turn by turn and diff against an eager store; compare the belief exam with the context exam; re-scan every structure by id; compare the eligible pool before and after a write.

Some checks are **ordered rather than parallel**. *"Never recalled"* is: is it in the store; if so does it claim a slot; if so is it in the eligible pool. Each answer makes the next question meaningful, and a guide that lists the three causes without the order sends you to the wrong module first.

And a guide is only trustworthy if its entries were **observed**. A predicted failure has no tell, because nobody has had to tell it apart from anything.

## Connections

<!-- graph:begin -->
**Taught in:** [The Failure Field Guide](../curriculum/advanced/failure-field-guide/index.md)

**Do not confuse with:** [Failure Class](failure-class.md)
<!-- graph:end -->
