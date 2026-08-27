---
id: retrieval-triggers
title: "Should I Even Look?"
level: intermediate
stage: retrieve
estimated_minutes: 35
concepts_taught: [retrieval-trigger]
concepts_required: [query-rewriting, read-path, write-path]
lessons_required: [query-formulation]
capstone_piece: memlab.retrieve.triggers
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Should I Even Look?

> **In one line.** Three of Priya's twenty-five turns actually ask the store for anything — Beginner retrieved on all of them, and a question mark turns out not to mean a question.

## Where this sits

<!-- graph:begin -->
**Stage:** `retrieve` · **Level:** intermediate · **~35 min**

**You need first:** [The Query Is Not the Last Message](../query-formulation/index.md)

**Concepts assumed:** [Query Formulation](../../../concepts/query-rewriting.md) · [The Read Path](../../../concepts/read-path.md) · [The Write Path](../../../concepts/write-path.md)
<!-- graph:end -->

## The problem

Every lesson in this module has improved *what* gets retrieved. None has asked *whether*.

Beginner retrieved on every turn, which is the default in most systems. Run the corpus through a trigger and the default looks expensive:

```
3 of 25 turns consult memory  (88% of Beginner's retrievals were needless)

  18  statement -- write path
   3  explicit recall
   3  correction -- new information, write path
   1  instruction -- new information, write path
```

Priya spends almost the whole conversation *telling* the system things. Three turns ask it for something.

The cost is not only latency. **A retriever always returns something**, so a needless retrieval produces five confident memories that had no business in the prompt — and this is a large part of why a taught procedure surfaces for a question about diet. If you always look, you always find.

## Why this isn't RAG

A RAG system retrieves per query because a query is, by construction, a request for information — that is the only kind of input it gets.

A memory layer sits in a *conversation*, where most turns are input rather than requests. The write path and the read path are triggered by different things, and conflating them means running a read on every write. There is no equivalent confusion in retrieval, because nobody sends a document-search system a statement about their diet.

## Mechanism

Two decisions, deliberately separated:

- **whether** to retrieve — this lesson
- **what shape** of memory to retrieve — `intent_of`, in [hybrid ranking](../hybrid-ranking/index.md)

And the subtle part: **a question mark does not mean a question.**

| turn | looks like | is |
|---|---|---|
| *"Can you keep answers shorter from now on?"* | a question | an **instruction** |
| *"I left Northwind last month, remember?"* | a question | a **correction** |
| *"Where do I work and what should I not eat?"* | a question | a question |

The first two are new information wearing interrogative punctuation. Retrieving for them is how an assistant ends up **arguing with a user who is correcting it** — it recalls the stale fact, finds it contradicts what was just said, and defends it. Session 9 is exactly that turn, and it is in the corpus because this failure is common.

Rules, in priority order: correction, then instruction, then explicit recall, then a question mark, then default. Corrections and instructions are checked *first* precisely because they can look like questions.

**The bias, where genuinely ambiguous, is toward retrieving.** A needless retrieval costs latency and a slot. A missing one looks like amnesia — and amnesia is the failure users actually report.

## Design decisions

**Rules or a classifier?** Rules, for now, and the honest caveat is that this is the weakest module in I6. Intent classification is a genuine language problem; a keyword list gets the clear cases and will misfile anything phrased unusually. It is defensible here because the cost of a miss is one needless retrieval, and because a model call on every turn to decide whether to *do work* is often more expensive than the work.

**Should a correction skip the write path too?** No — the opposite. A correction is the highest-value write there is: it is the user telling you a belief is wrong. It skips *retrieval*, not ingestion.

**Retrieve on ambiguity or skip?** Retrieve. The two errors are not symmetric — one is a wasted ranking pass, the other is a system that appears to have forgotten.

## Lab

**You'll implement:** `decide`, with the rule ordering that matters.

**Run:**
```
uv run python curriculum/intermediate/retrieval-triggers/lab/lab.py
```

**Expected output:** **3 of 25** turns retrieving, the reason breakdown above, and the three turns named — the Spark job recall, the weekly report invocation, and session 14.

**Stretch:** the word *remember* appears in both cue tables, split by phrasing — `"do you remember"` asks the store, `"remember?"` tells it. Move `"remember?"` into `RECALL` and re-run: session 9 now retrieves, and the assistant is about to recall the stale employer at the exact moment Priya is correcting it.

**Which list a cue lives in is the policy**, and this split was found by looking for the turn that gets it wrong rather than by reasoning about the word.

## What this adds to the capstone

`memlab.retrieve.triggers` — `decide`, `should_retrieve`, and the cue tables.

**I6 ends here, and the milestone's target is met.** The exam is answered correctly **from the assembled context at k=5** under `--profile intermediate`, and fails under every earlier snapshot. `memlab` v0.2-beta.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Assistant argues with a correction | Retrieving on a corrective turn | Correct it mid-conversation; see if it defends the old fact | Check corrections first |
| Irrelevant memories in every reply | Retrieving unconditionally | Count retrievals against turns that asked for anything | A trigger |
| System looks like it forgot | Trigger too strict | Ask something indirectly | Bias toward retrieving |
| Latency on turns that need nothing | No trigger | Profile retrieval calls per conversation | Skip statements |
| An instruction is treated as a query | Rule order wrong | Test "can you keep answers shorter?" | Instructions before questions |

## Check yourself

??? question "88% of retrievals were needless. Was Beginner wrong to retrieve unconditionally?"
    It was the right default for a system with no trigger, because the alternative was a rule that might skip a turn that needed memory. What makes it wrong *now* is that the cost became visible: every needless retrieval produces five memories that compete for the same slots as a real recall.

??? question "'Remember' appears in both cue tables. Isn't that a contradiction?"
    It is the same word doing two jobs, split by phrasing. *"Do you remember where I work?"* asks the store; *"I'm at Calico now, remember?"* tells it. Putting the bare `"remember?"` in the recall list makes the assistant retrieve a stale fact precisely when it is being corrected — which is how the split was found.

??? question "This is the weakest module in I6. Why ship it?"
    Because the measurement is solid even where the classifier is not: whatever the exact threshold, the great majority of conversational turns are not requests, and a system retrieving on all of them is doing avoidable work and producing avoidable noise. The rules are a starting policy; the 88% is the finding.

## Connections

<!-- graph:begin -->
**Stage:** `retrieve` · **Level:** intermediate · **~35 min**

**You need first:** [The Query Is Not the Last Message](../query-formulation/index.md)

**Concepts assumed:** [Query Formulation](../../../concepts/query-rewriting.md) · [The Read Path](../../../concepts/read-path.md) · [The Write Path](../../../concepts/write-path.md)
<!-- graph:end -->
