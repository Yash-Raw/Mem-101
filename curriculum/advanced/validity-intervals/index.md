---
id: validity-intervals
title: "Validity Intervals"
level: advanced
stage: store
estimated_minutes: 50
concepts_taught: [validity-interval, as-of-query]
concepts_required: [bi-temporal-modeling, supersession]
lessons_required: [two-clocks]
capstone_piece: memlab.temporal.validity
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Validity Intervals

> **In one line.** Build the two-axis query, fix the two clocks feeding it, and then measure that on 549 days of corpus the two axes never once disagree — because nothing has yet read a date off a sentence.

## Where this sits

<!-- graph:begin -->
**Stage:** `store` · **Level:** advanced · **~50 min**

**You need first:** [Two Clocks](../two-clocks/index.md)

**Concepts assumed:** [Bi-Temporal Modeling](../../../concepts/bi-temporal-modeling.md) · [Supersession](../../../concepts/supersession.md)

**This unlocks:** [Three Temporal Questions](../temporal-questions/index.md)
<!-- graph:end -->

## The problem

*"What did you believe about my employer in June 2025?"*

Level 2's read path answers with four memories, every one of them about Calico Systems — a job she had not been offered yet. It is not a ranking failure. `live_only` is a filter on **belief** time with its clock pinned to *now*, and the question is about **event** time. There is no bug to find; the query cannot be expressed.

The memory that answers it correctly is in the store, carrying both instants that prove it: *"Priya is a data engineer at Northwind Labs"*, true from 2025-03-04, retired 2025-12-08. **The data is sufficient. The query is not expressible.**

## Why this isn't RAG

A retrieval system answers *"what does the corpus say?"* and the corpus is a fixed thing that does not have opinions about when. If you want a past state you keep a snapshot of the index, because the index has no internal notion of its own history.

A memory layer holds beliefs that were formed, held, and withdrawn — and the withdrawal is data. *"When did you stop believing this, and were you right to?"* is a question about the store's own history that no amount of re-indexing answers, because the answer is not in the documents. It is in the two intervals the record kept while nobody was reading them.

## Mechanism

**Two predicates, one query.**

```python
held_at(m, when)      # valid_from <= when < valid_to      -- was it TRUE
believed_at(m, when)  # recorded_at <= when < invalid_at   -- did we HOLD it

as_of(memories, when)                        # today's account of that day
as_of(memories, when, believed_at_time=t)    # the account we'd have given at t
```

Omit the second clock and you get the store's *current* account of the past, corrections included. Pass it and you get the account it would have given then, mistakes and all. Both are legitimate; conflating them is how an audit trail stops being one.

An open `valid_to` reads as *"still true as far as anyone said"*. That is the honest reading — nothing in the corpus says the cycling stopped, only that a later memory mentions a train.

### Three things had to be fixed before the query meant anything

**1 · The belief clock was the wall clock.** `recorded_at` defaulted to `datetime.now()`, so a seventeen-month conversation collapsed to a **single instant** — the moment the ingest process happened to run, different on every run. Ask the store what it believed in June 2025 and it answers *nothing*, because it believed everything as of this morning.

```
distinct recorded_at dates    1  ->  15
```

**2 · `invalid_at` was answering two questions.** The code said so out loud: *"a belief is invalid from the moment its replacement became true"*. That sentence defines `valid_to`. Used as `invalid_at`, it produced a record retired **nine months before it was written** — the travel agent's Berlin claim, recorded 2026-05-16, retired 2025-08-02 on the date Priya gave her address.

**A belief cannot end before it begins.** One field was answering two questions, so both answers were wrong, in different situations.

**3 · Nothing recorded that anything stopped.**

Both columns are measured *before this module's parser lands* — `at("A1")`
with `anchor=None`, which is the state the next two lessons build on. Shipped
`at("A1")` anchors four phrases and moves the last row.

| | `@I8` | this module |
|---|--:|--:|
| facts with a recorded end | 0 | **7** |
| beliefs retired before they were recorded | **1** | **0** |
| *"what is true now?"* → employer facts | **5** | **4** |
| *"what was true in June 2025?"* | ✓ Northwind | ✓ Northwind |
| *"what did we believe in June 2025?"* | ✓ Northwind | ✓ Northwind |

Note which row the split fixes. The past was already answerable once the query existed — the `@I8` data was sufficient. What the split fixes is **the present**: without event ends, every fact is still open, so *"what is true now"* returns the dead Northwind job alongside the live Calico one. `live_only` gets that right by accident, filtering on the belief axis for a question about the event axis, and the accident holds only while the two clocks are the same.

### And they are the same. Every day, for 549 days.

Sweep the corpus and compare the two questions on each date — still with the
parser off, since nothing has yet written a `valid_from`:

```
dates where "true then" and "believed then" differ:   0 of 549
```

Not one. The rectangle is a line. Both axes are populated, both predicates are correct, and the model is **degenerate** — because every event time in the store is still the instant the record was written, exactly as `two-clocks` measured.

Anchor a single phrase by hand — *"before the move"* to 2025-08-02, the one date `gold.yml` gives for it — and re-run the sweep:

```
after anchoring one phrase:                         250 of 549
```

One parsed date separates the axes on **46% of the days in the corpus**. The machinery was never the constraint.

## Design decisions

**Why fix the clocks here rather than in `two-clocks`?** Because until this query existed there was no way to see that they were broken. A single `recorded_at` looks fine in every Level 2 test; it fails only when something asks a question along that axis. Fixing an input to a query you cannot run is how you get a parser that is confidently wrong for two modules.

**Why is the split gated behind A1 rather than just applied?** Because 31 Intermediate lessons quote figures measured against the old single-instant semantics. `pipeline.bitemporal` switches it, `@I1`–`@I8` are verified identical by snapshot diff, and `two-clocks` audits `at("I8")` — the system as Level 2 actually shipped. An Advanced improvement that silently moves an Intermediate number is a build break, not an improvement.

**And this lesson pins its own sub-state.** A1 switches on two things: the bi-temporal split, here, and the relative-time parser two lessons later. Every figure above is measured with `at("A1").with_stage(anchor=None, ...)`, because `relative-time-resolution` exists precisely to move the last one — from 0 of 549 to 257. Quoting `at("A1")` for both would make one of the two lessons wrong the moment the other landed.

**Why not close every interval by inferring from supersession?** Because the retirement date is when the *system found out*, not when the world moved. The corpus says she left Northwind in December and told you in January; deriving `valid_to` from `invalid_at` puts the end of the job on the day she mentioned it and reintroduces precisely the conflation this module exists to remove. It would look correct here, which is what makes it dangerous.

**Is a degenerate bi-temporal model worth shipping?** Yes, and this is the uncomfortable one. It costs two nullable columns and answers nothing today. It is worth it because the alternative is backfilling two clocks onto a store that never recorded them, and **an event time you did not capture at write time cannot be reconstructed afterwards** — the sentence is gone.

## Lab

**You'll implement:** `held_at`, `believed_at`, and `as_of`.

**Run:**
```
uv run python curriculum/advanced/validity-intervals/lab/lab.py
```

**Expected output:** the June 2025 question answered — one memory, Northwind — then the `@I8` vs `@A1` table with **0 → 7** event ends and **5 → 4** on *"true now"*, then the sweep: **0 of 549**, and **250 of 549** after one phrase is anchored.

**Stretch:** find a date where `as_of(when)` and `as_of(when, believed_at_time=when)` disagree, without anchoring anything. You cannot; the answer is the lesson. Then work out how many phrases you would have to anchor before the distinction pays for the two columns.

## What this adds to the capstone

`memlab.temporal.validity` — `held_at`, `believed_at`, `as_of`, `changed_between`. `Memory.supersede` gains `found_out` and `event_end`; `reconcile` gains `bitemporal`; `Pipeline.bitemporal` switches it on at A1. `recorded_at` now comes from the turn rather than `now()` in both the staged extractor and the agent-write path — which also makes the record deterministic between runs, and moved no `@I*` figure.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| As-of query returns nothing | Belief clock is the ingest wall clock | Count distinct `recorded_at` values | Stamp from the turn |
| A belief retired before it was recorded | `invalid_at` set from the winner's event time | Assert `recorded_at <= invalid_at` | Split the two instants |
| "What is true now" returns dead facts | No event ends; every interval open | Count `valid_to` | Close on supersession |
| Two axes that never disagree | No event time read from language | Sweep both queries over the corpus | Anchor the phrases |
| Backfill is impossible later | Clocks not captured at write time | Try to reconstruct one | Capture both from the start |

## Check yourself

??? question "The store answered June 2025 with four facts about Calico. Which layer is wrong?"
    None of them, which is the point. Retrieval ranked correctly, arbitration retired the right memory, and `live_only` did exactly what I4 specified. The question was asked along an axis the read path does not have, so every layer answered a different question correctly. Adding a reranker would not have moved it.

??? question "`valid_to` and `invalid_at` are both set when a memory is superseded. Why two fields?"
    Because they diverge in both directions. The Berlin claim was retired on a date nine months before it was recorded — legal on one axis, impossible on the other. And a belief retired in error leaves the fact true while the belief is gone. One field cannot hold both, and the gap between them is the answer to "how long were you wrong?".

??? question "Zero of 549 days distinguish the axes. Was the bi-temporal model a waste?"
    It would have been, if the plan were to stop here. The measurement says the machinery is not the binding constraint — the input is — which is a result about *where to work next*, not a verdict on the design. The trap is the opposite conclusion: shipping one clock now because two look redundant today, and discovering in a year that the sentences you would need to re-read are gone.

## Connections

<!-- graph:begin -->
**Stage:** `store` · **Level:** advanced · **~50 min**

**You need first:** [Two Clocks](../two-clocks/index.md)

**Concepts assumed:** [Bi-Temporal Modeling](../../../concepts/bi-temporal-modeling.md) · [Supersession](../../../concepts/supersession.md)

**This unlocks:** [Three Temporal Questions](../temporal-questions/index.md)
<!-- graph:end -->
