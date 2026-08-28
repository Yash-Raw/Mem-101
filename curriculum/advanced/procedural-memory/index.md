---
id: procedural-memory
title: "Procedural Memory"
level: advanced
stage: store
estimated_minutes: 45
concepts_taught: [procedural-memory, step-order]
concepts_required: [memory-record, extraction-pipeline]
lessons_required: [cold-start-and-shared-accounts]
capstone_piece: memlab.procedural.steps
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Procedural Memory

> **In one line.** Two memories are typed `PROCEDURAL` and one of them is a comment about a procedure — split it on commas and you get a plausible two-step workflow that does not exist.

## Where this sits

<!-- graph:begin -->
**Stage:** `store` · **Level:** advanced · **~45 min**

**You need first:** [Cold Start and Shared Accounts](../cold-start-and-shared-accounts/index.md)

**Concepts assumed:** [The Memory Record](../../../concepts/memory-record.md) · [The Extraction Pipeline](../../../concepts/extraction-pipeline.md)

**This unlocks:** [Learning From Outcomes](../learning-from-outcomes/index.md)
<!-- graph:end -->

## The problem

Session 6, two consecutive turns:

```
Here's how I do my weekly report, memorise this. Pull the pipeline metrics
from the warehouse, diff against last week, flag anything over 15% drift,
then write it up in the shared doc. Always in that order.

The diff step matters most. If you skip it the numbers look fine and they aren't.
```

Two memories come out, both typed `PROCEDURAL`. The first is a workflow whose order is load-bearing and whose order **survives** — `extract/atomise.py` refuses to split procedural memories, and that refusal is the only reason:

```
1. pull pipeline metrics from the warehouse
2. diff against last week
3. flag anything over 15% drift
4. write it up in the shared doc      order matches gold: True
```

The second is *"In Priya's weekly report, the diff step matters most"* — a claim **about** the procedure, stored beside it with nothing connecting them.

## Why this isn't RAG

Order is not a property a retrieval system has to preserve, because it never took anything apart. A document arrives whole, is indexed whole, and comes back whole; the steps of a recipe stay in sequence because nobody had an opportunity to reorder them.

A memory layer's write path *atomises* — it exists to break statements into independently retrievable facts, which is exactly the wrong operation for a workflow. The four steps are not four facts. **The sequence is the content**, and preserving it requires the extractor to make an exception it has to be told about.

## Mechanism

**The refusal is the mechanism.** `atomise` has a `PROCEDURAL` branch that returns the content unsplit. Everything downstream — dedupe, arbitration, packing — then treats a four-step workflow as one memory, which is correct and is why the order is still there at read time.

**Parsing it back is a recovery, not a design.** Splitting the stored sentence on commas works here and is fragile by construction: the write path stored prose, so prose is what there is. A procedure captured as a list at extraction time would need none of this, and the reconstruction is the price of not having done that.

**The annotation is typed the same as the procedure**, and that is the failure worth having:

```
what the annotation would have become:
   ['In Priya's weekly report', 'the diff step matters most']
```

A well-formed two-step workflow, in the store, indistinguishable from a real one. The type system says *procedural* and means *about a procedure* — the extractor had no way to express the difference. Excluding it takes a check for the annotation pattern, and **dropping it is better than parsing it, because a wrong procedure looks like data**.

**Nothing links them.** `derived_from` on the annotation is empty. The two came from adjacent turns and the extractor treated each independently, so attaching *"the diff step matters most"* to the workflow means matching on content — and `retrieving-procedures` measures what happens when only one of the pair is retrieved.

### What the recovered procedure knows

```
procedural memories in the store   2
procedures recovered              1
critical step                     'diff' at position 2 of 4
```

Position 2 of 4 is the useful part: the step the user singled out is neither first nor last, so no ordering heuristic would have found it. It is knowable only because they said so.

## Design decisions

**Why not add a `Procedure` type to the record?** Because `MemoryType` has four members with distinct lifecycles and update rules, and a fifth for *"annotation about a procedure"* is a category the extractor cannot reliably assign — it would be wrong on the first unusual phrasing, and a mistyped record is harder to notice than an unparsed one. The check lives where the ambiguity is.

**Why parse on read rather than fix extraction?** Fixing extraction is right and it is not free: the fixtures that produce these two memories are authored, and changing them moves the store shape every level is measured against. The recovery is honest about being a workaround, and `learning-from-outcomes` is where the representation earns a change.

**Why does `order_preserved` take the expected steps?** Because there is no way to verify an order against itself. The check is against `gold.yml`, which is the answer key precisely so that claims like *"the order survived"* are testable rather than asserted — and it caught a transcription error in gold on the way through: the corpus says *"write it up"* and gold said *"write up"*.

## Lab

**You'll implement:** `parse`, `build`, and `order_preserved`.

**Run:**
```
uv run python curriculum/advanced/procedural-memory/lab/lab.py
```

**Expected output:** **2** procedural memories, **1** procedure recovered, the four steps in gold order, the critical step `'diff'` at **position 2 of 4**, and the two-step non-procedure the annotation would have produced.

**Stretch:** remove the annotation check from `build`. You get two procedures, both well-formed, and every test passes except the one that counts them. **A wrong procedure is not noisy — it is a workflow someone might follow.**

## What this adds to the capstone

`memlab.procedural.steps` — `Procedure`, `parse`, `annotation`, `build`, `order_preserved`. No pipeline stage: the procedure is already stored correctly, and what this adds is the ability to read it as a sequence rather than a sentence.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Steps come back shuffled | Procedure atomised into facts | Check the extractor's type branch | Refuse to split |
| A workflow that never existed | Comment about a procedure parsed as one | Count procedures against procedural memories | Detect and drop annotations |
| Critical step lost | Annotation stored unlinked | Check `derived_from` on it | Attach, or match on content |
| Order verified against itself | No independent expectation | Compare with the answer key | `gold.yml` |
| Fragile parse | Structure discarded at write time | Reword the source sentence | Capture the list at extraction |

## Check yourself

??? question "Both memories are typed `PROCEDURAL`. Is that a bug in the extractor?"
    It is a limit rather than a bug. *"The diff step matters most"* genuinely is about a procedure, and the four types describe lifecycles — episodic, semantic, procedural, working — not the difference between a thing and a remark about it. The extractor assigned the only type that fits. What is missing is a way to say *annotation*, and inventing a fifth type would be wrong on the first phrasing that did not match.

??? question "Why is dropping the annotation better than parsing it into two steps?"
    Because the parse succeeds. It produces a well-formed procedure that reads like the real one, enters the store, and would be returned to someone asking how to do something. An unparsed memory is visibly incomplete; a wrongly parsed one is a workflow with the same shape as a correct workflow, and nothing downstream distinguishes them.

??? question "The critical step is second of four. Why does that matter?"
    Because no positional heuristic recovers it. First and last are the positions a system might guess at; the middle is only knowable because the user said so, in a separate sentence, in a separate memory, with no link between them. The information exists and the structure to hold it does not.

## Connections

<!-- graph:begin -->
**Stage:** `store` · **Level:** advanced · **~45 min**

**You need first:** [Cold Start and Shared Accounts](../cold-start-and-shared-accounts/index.md)

**Concepts assumed:** [The Memory Record](../../../concepts/memory-record.md) · [The Extraction Pipeline](../../../concepts/extraction-pipeline.md)

**This unlocks:** [Learning From Outcomes](../learning-from-outcomes/index.md)
<!-- graph:end -->
