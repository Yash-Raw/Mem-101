---
id: golden-conversation
title: "Golden Conversation"
kind: concept
stage: govern
contrasts_with: [pinned-assertion]
related: [absent-corpus, eval-suite, moving-ground-truth]
status: published
---

# Golden Conversation

One frozen transcript that every lab, level and metric is measured against.

## Why it matters in a memory layer

It is what makes pinned numbers affordable. Against a fixed corpus, `== 37` is a claim about the system. Against a changing one it is a claim about the corpus **and** the system at once — failing periodically for reasons nobody can attribute, until someone rationally deletes the assertions and removes the only regression suite there was.

The dependency is proportional: this course has **331** pinned literals, so the corpus is 331 times load-bearing. Change one timestamp in it and dozens of assertions fail across lessons that have nothing to do with each other, and not one failure names the corpus.

That is the cost of the approach, and it buys the thing a stateful system most needs — an accumulated store whose numbers are reproducible, so that a change can be attributed to the change.

## Connections

<!-- graph:begin -->
**Taught in:** [Regression Testing a Stateful System](../curriculum/advanced/regression-testing-state/index.md)

**Do not confuse with:** [Pinned Assertion](pinned-assertion.md)
<!-- graph:end -->
