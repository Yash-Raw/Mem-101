---
id: moving-ground-truth
title: "Moving Ground Truth"
kind: concept
stage: govern
contrasts_with: [absent-corpus]
related: [as-of-query, supersession, validity-interval]
status: published
---

# Moving Ground Truth

The correct answer depends on when the question is asked, so an answer key with one value per question is asserting something false.

## Why it matters in a memory layer

*"Where does Priya work?"* has two right answers in this course's corpus and both are in the transcript. A benchmark that picks one is asserting that memory does not change — the single thing it certainly does.

The fix is the one `as-of-query` already made for reads: **date the assertions**. *"Employer was Northwind in session 1 and Calico from session 8"* is two claims with timestamps rather than one contested fact, and it is machine-checkable precisely because it is dated. Six of this course's nine gold seams are supersessions for that reason.

The related trap is attribution. A wrong answer implicates every stage between the turn and the reply — **seven** here — so a single end-to-end score can detect a regression and never locate one.

## Connections

<!-- graph:begin -->
**Taught in:** [Why Memory Eval Is Hard](../curriculum/advanced/why-memory-eval-is-hard/index.md)

**Do not confuse with:** [The Absent Corpus](absent-corpus.md)
<!-- graph:end -->
