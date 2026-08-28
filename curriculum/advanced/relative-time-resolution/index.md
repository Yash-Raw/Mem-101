---
id: relative-time-resolution
title: "Resolving 'Last Week'"
level: advanced
stage: extract
estimated_minutes: 50
concepts_taught: [relative-time]
concepts_required: [bi-temporal-modeling, validity-interval, procedural-memory]
lessons_required: [temporal-questions]
capstone_piece: memlab.temporal.anchor
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Resolving "Last Week"

> **In one line.** Six relative references, four classes, and the one you must not resolve is a step inside a recipe.

## Where this sits

<!-- graph:begin -->
**Stage:** `extract` · **Level:** advanced · **~50 min**

**You need first:** [Three Temporal Questions](../temporal-questions/index.md)

**Concepts assumed:** [Bi-Temporal Modeling](../../../concepts/bi-temporal-modeling.md) · [Validity Interval](../../../concepts/validity-interval.md) · [Procedural Memory](../../../concepts/procedural-memory.md)

**This unlocks:** [Temporal Knowledge Graphs](../temporal-knowledge-graphs/index.md)
<!-- graph:end -->

## The problem

`validity-intervals` left a promise: the bi-temporal model is degenerate — the two axes disagree on **0 of 549 days** — because nothing reads an event date off a sentence, and anchoring one phrase by hand moved that to 250.

Six memories in the corpus carry a relative reference. They are not one problem:

| phrase | class | resolvable by |
|---|---|---|
| *"...last week"* (gluten diagnosis) | **offset** | arithmetic on the turn clock |
| *"...last month"* (left Northwind) | **offset** | arithmetic — but see below |
| *"since March 2026"* | **interval** | parsing; opens `valid_from`, no end |
| *"before the move"* | **event** | a lookup into the store |
| *"diff against last week"* | **literal** | **nothing. Leave it alone.** |
| *"Sam still works nights"* | none | no reference to resolve |

The fifth is the expensive one. It is a step inside a taught procedure — *pull metrics, **diff against last week**, flag drift over 15%* — and a parser that fires on every match rewrites the recipe into a claim that the procedure was true on a Tuesday in September.

## Why this isn't RAG

Document time is metadata. A file has a modification date, an article has a byline date, and where a document does contain "last week" it is quoting someone — the reader resolves it, or does not, and the index is unaffected either way.

In a memory layer the phrase *is* the data. *"Last week"* is the only statement of when the fact became true, it is an offset from an instant the sentence does not contain, and nothing later can recover it: the turn scrolls out of the window and the anchor is gone. **The resolution has to happen on the write path or not at all** — which is the general shape of this whole course.

## Mechanism

**Classify before resolving, and let the classifier decline.** Four classes and a fifth answer of *"no reference here"*. The order matters: `EVENT` is tested before `OFFSET`, because *"used to cycle to work before the move"* contains no offset and arithmetic would skip it silently.

**A procedure's steps are instructions, not claims about when.** The guard is one condition — `type is PROCEDURAL` — and it is the difference between storing a workflow and storing a corrupted one. This is why `procedural-memory` is a prerequisite: you have to know the type exists before you can refuse to parse it.

**An offset carries the precision of its unit.** *"Last week"* is a span of days and subtracting seven is right. *"Last month"* names a calendar unit — **December**, not "thirty days ago" — and treating it as `timedelta(days=30)` lands on **2025-12-20**, nineteen days from the truth. Two words, two different kinds of arithmetic:

```
last month, as 30 days      2025-12-20      19 days wrong
last month, as a calendar   2025-12-01      exact
```

**An event reference needs the store, not the clock.** *"Before the move"* resolves only by finding the memory that dates the move — which makes it the one class that can fail, and failing is a legitimate answer. A parser that always produces a date is a parser that invents them.

### The result

All four resolvable phrases land exactly on `gold.yml`:

| phrase | resolved | gold | error |
|---|---|---|--:|
| before the move | 2025-08-02 | 2025-08-02 | **0d** |
| left Northwind Labs last month | 2025-12-01 | 2025-12-01 | **0d** |
| gluten intolerance last week | 2026-05-08 | 2026-05-08 | **0d** |
| since March 2026 | 2026-03-01 | 2026-03-01 | **0d** |

Down from 249, 49 and 7 days. And the model stops being degenerate:

```
dates where "true then" and "believed then" differ:   0 of 549  ->  257 of 549
```

Four parsed dates separate the two axes on **47% of the corpus**.

### The audit undercounts, in the honest direction

`two-clocks` measures progress as *"event times that are not a write instant"*. After anchoring it reports **3**, and four memories were anchored. The missing one is *"before the move"*, which resolves to 2025-08-02 11:15 — the exact instant of the turn where she gave her new address, because that turn is the evidence for the move.

A genuinely derived date that happens to coincide with a write instant is invisible to the heuristic. That is the direction you want to be wrong in: it **undercounts** progress and never claims a clock is running when it is not.

## Design decisions

**Why not have the extractor emit dates directly?** Because it cannot resolve *"before the move"* — that needs the whole store, and the extractor sees one turn. Anchoring runs as a consolidation pass for the same reason entity resolution does.

**Why anchor before reconciliation?** Arbitration is recency-wins on the event clock. Resolving *"last month"* after the fact has already lost an argument is resolving it too late, and the ordering is not visible from either module alone.

**Why a table of event markers rather than a general resolver?** Because *"before the move"* → *find the memory that dates a move* is a research problem, and the failure mode of guessing is a confident wrong date that nothing downstream can question. Twelve explicit patterns that decline loudly beat a resolver that succeeds plausibly. The same argument as `temporal-questions` made for its classifier, in the module where the cost is highest.

**Why leave `happened_at` alone?** It means *"when this was asserted"* and a dozen Level 1 and 2 figures are measured against it. The parser writes `valid_from`; `event_start` prefers it and falls back. Nothing earlier moves.

## Lab

**You'll implement:** `classify` and `resolve`.

**Run:**
```
uv run python curriculum/advanced/relative-time-resolution/lab/lab.py
```

**Expected output:** the six references with their classes, then the four resolutions at **0d** error against `gold.yml`, then the sweep moving from **0 of 549** to **257 of 549** — and the procedure step reported untouched.

**Stretch:** delete the `PROCEDURAL` guard and re-run. The weekly report gains a `valid_from` of 2025-09-07, and every test still passes except the one that checks the recipe. **A parser with no way to decline will always find something.**

## What this adds to the capstone

`memlab.temporal.anchor` — `Anchor`, `Resolution`, `classify`, `resolve`, `anchor_all`. Wired as `Pipeline.anchor` at A1, running before reconciliation. `@I1`–`@I8` unmoved; `validity-intervals` pins `at("A1").with_stage(anchor=None, ...)` so its numbers stay true.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| A recipe becomes a dated claim | Parser fired inside a procedure | Check `valid_from` on procedural memories | Refuse by type |
| Month offsets 19 days out | Calendar unit treated as a fixed delta | Resolve a phrase said mid-month | Unit-aware arithmetic |
| Event references silently skipped | Offset patterns tested first | Count classes, not resolutions | Order the classifier |
| Confident wrong dates | Resolver guesses rather than declines | Ask what it does with an unknown event | Return unresolved |
| Anchoring changes nothing downstream | Ran after arbitration | Check which fact won | Anchor before reconcile |

## Check yourself

??? question "Why is *"diff against last week"* the most expensive of the six?"
    Because it is the only one where resolving looks like success. The other failures are visible — an unresolved phrase stays where it was, and an event lookup that fails returns nothing. Writing a `valid_from` onto a procedure produces a well-formed record that says the workflow was true in September, and no test that only checks for the presence of dates will ever catch it.

??? question "The audit reports 3 anchored memories and 4 were anchored. Which number is wrong?"
    Neither. The audit asks a proxy question — *is this event time a write instant?* — and *"before the move"* resolves to exactly the turn where the move was mentioned, because that turn is the evidence. The proxy undercounts, which is the safe direction: it will never report a clock as running when it is not.

??? question "Four dates changed. Why does that move 257 days of the corpus?"
    Because an interval is a span, not a point. Moving one `valid_from` earlier makes that memory true across every day between the new date and the old one, and on each of those days the store now believes something it did not yet believe — the two axes disagree. Four facts, a few months each, and half the corpus separates.

## Connections

<!-- graph:begin -->
**Stage:** `extract` · **Level:** advanced · **~50 min**

**You need first:** [Three Temporal Questions](../temporal-questions/index.md)

**Concepts assumed:** [Bi-Temporal Modeling](../../../concepts/bi-temporal-modeling.md) · [Validity Interval](../../../concepts/validity-interval.md) · [Procedural Memory](../../../concepts/procedural-memory.md)

**This unlocks:** [Temporal Knowledge Graphs](../temporal-knowledge-graphs/index.md)
<!-- graph:end -->
