---
id: judge-role
title: "Judge Role"
kind: concept
stage: govern
contrasts_with: [memory-operations]
related: [bounded-output, provenance, eval-suite]
status: published
---

# Judge Role

The distinction between asking a model to *generate* candidates, to *judge* a relation, and to *arbitrate* which belief survives — the last of which it must never do.

## Why it matters in a memory layer

Judging a retrieval answer is comparatively safe: the judge scores against documents that still exist, a human can read both, and a wrong call produces a wrong *number*. A judge in a memory system decides what is **stored** — its output is state, not a score, and a wrong call retires a true belief permanently with no reason anyone can inspect.

So the split this course made two levels earlier is load-bearing: *the model says these two disagree, and rules say this one wins.* Detection is a language question; arbitration is a policy whose output changes what is believed and therefore has to be explainable. A model there produces a store whose contents depend on sampling, and *"why do you think that?"* has no answer.

Generation is judged differently again. This system's two generation sites are unbounded and unscored, and that is acceptable because **nothing downstream trusts them** — four later stages exist precisely because extraction over-produces.

## Connections

<!-- graph:begin -->
**Taught in:** [LLM as Judge, and Its Failure Modes](../curriculum/advanced/llm-as-judge-for-memory/index.md)

**Do not confuse with:** [Memory Operations](memory-operations.md)
<!-- graph:end -->
