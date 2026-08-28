---
id: pinned-assertion
title: "Pinned Assertion"
kind: concept
stage: govern
contrasts_with: [golden-conversation]
related: [eval-suite, flat-metric, memory-record]
status: published
---

# Pinned Assertion

A test comparing against a literal number that was measured, not specified.

## Why it matters in a memory layer

A memory system emits counts, ranks and token budgets rather than pass/fail, so the only faithful record of correct behaviour is the number someone measured. About **half** the tests in this course are of this kind — not by policy, but because writing down what was measured *is* the test.

The danger is reading one as a specification. `assert len(store.all()) == 37` records what the system did when someone last looked; updating it to match a change converts a regression detector into a rubber stamp. Every one here is anchored to a **module snapshot**, so a moved number can be bisected to the module that moved it instead of reasoned about.

Resist tolerances. A drift budget is a decision about acceptable change, made once and applied everywhere by someone who cannot know which numbers matter — and on this course a five-token budget move was the finding.

## Connections

<!-- graph:begin -->
**Taught in:** [Regression Testing a Stateful System](../curriculum/advanced/regression-testing-state/index.md)

**Do not confuse with:** [Golden Conversation](golden-conversation.md)
<!-- graph:end -->
