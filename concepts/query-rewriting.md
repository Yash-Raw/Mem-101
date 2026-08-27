---
id: query-rewriting
title: "Query Formulation"
kind: concept
stage: retrieve
contrasts_with: []
related: [hybrid-ranking,slot,coreference]
status: published
---

# Query Formulation

Transforming the user's message into the query the store should actually be asked: resolving pronouns to the account holder, splitting compound questions, and identifying which attributes are being asked about.

## Why it matters in a memory layer

The last message is rarely a good query. "Where do I work" names nobody until *I* is resolved, so memories about a partner compete on equal footing. A compound question embeds to something that matches everything mediocrely — the same fact ranks 2nd for the compound form and 1st for its own half. And a question can share **no words** with the fact that answers it: "what should I not eat" against "has a gluten intolerance". Only mapping the question to a slot bridges that.

## Connections

<!-- graph:begin -->
**Taught in:** [The Query Is Not the Last Message](../curriculum/intermediate/query-formulation/index.md)

**Used in:** [Should I Even Look?](../curriculum/intermediate/retrieval-triggers/index.md)
<!-- graph:end -->
