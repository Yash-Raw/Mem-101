---
id: coverage-vs-knowledge
title: "Coverage vs Knowledge"
kind: concept
stage: retrieve
contrasts_with: [user-model]
related: [entity-resolution, disclosure, volatility]
status: published
---

# Coverage vs Knowledge

How many attributes a model has, against whether those attributes contain the facts a question needs.

## Why it matters in a memory layer

Coverage is cheap — count the keys, no question required — so it is the number that gets wired to a readiness check. It is also the one that goes green first. On this course's corpus the model reaches all six attributes at **turn 20** and cannot answer the exam until **turn 22**, because a required fact arrives inside an attribute it already had.

Two turns of a gate reporting ready while the answer does not exist, in exactly the window where being confidently wrong is most likely.

A partial model is not dangerous by itself: keyed on slots, it answers what it covers and stays silent elsewhere, so cold start needs no special mode. What is dangerous is measuring readiness with the metric that does not require knowing the question.

## Connections

<!-- graph:begin -->
**Taught in:** [Cold Start and Shared Accounts](../curriculum/advanced/cold-start-and-shared-accounts/index.md)

**Do not confuse with:** [User Model](user-model.md)
<!-- graph:end -->
