---
id: dropped-clause
title: "Dropped Clause"
kind: concept
stage: extract
contrasts_with: [over-extraction]
related: [lessons-learned, extraction-pipeline, procedural-memory]
status: published
---

# Dropped Clause

The half of a sentence extraction discards — typically the conditional, which is the half that justifies the rest.

## Why it matters in a memory layer

An extractor is tuned to produce durable assertions, and a conditional is not one. *"If you skip it the numbers look fine"* is a fact about a counterfactual, so it is dropped every time — and it is the only part that could ever be checked or contested.

Retrieval never faces this: both clauses live in the same passage, and anything that surfaces one surfaces the other.

The measurement has to run over the **transcript**, not the store. A feature reading the store finds nothing and concludes the user never explains their reasoning, when in fact they explained it and the write path kept only the conclusion. Once a clause is dropped, no amount of reading the store recovers it.

## Connections

<!-- graph:begin -->
**Taught in:** [Learning From Outcomes](../curriculum/advanced/learning-from-outcomes/index.md)

**Do not confuse with:** [Over-Extraction](over-extraction.md)
<!-- graph:end -->
