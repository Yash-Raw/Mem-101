---
id: retrieval-trigger
title: "Retrieval Triggers"
kind: concept
stage: retrieve
contrasts_with: []
related: [query-rewriting,read-path,write-path]
status: published
---

# Retrieval Triggers

Deciding whether a turn should consult memory at all, before deciding what to retrieve.

## Why it matters in a memory layer

Retrieving on every turn is the default and is wrong most of the time — measured on this corpus, **3 of 25 turns** genuinely ask the store for anything; the rest are the user telling it things. Every needless retrieval spends a ranking pass and, worse, produces an answer, because a retriever always returns *something*. The subtlety is that a question mark does not mean a question: "can you keep answers shorter?" is an instruction and "I left Northwind, remember?" is a correction. Both are new information, and retrieving for them is how an assistant ends up arguing with a user who is correcting it.

## Connections

<!-- graph:begin -->
**Taught in:** [Should I Even Look?](../curriculum/intermediate/retrieval-triggers/index.md)
<!-- graph:end -->
