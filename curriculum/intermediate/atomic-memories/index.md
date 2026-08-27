---
id: atomic-memories
title: "Atomic Memories"
level: intermediate
stage: extract
estimated_minutes: 35
concepts_taught: []
concepts_required: [atomic-fact, extraction-pipeline, procedural-memory]
lessons_required: [extraction-quality]
capstone_piece: memlab.extract.atomise
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Atomic Memories

> **In one line.** Atomicity exists to keep memories updatable — so the rule is exactly as strong as that purpose, and a procedure is the case where obeying it destroys the memory.

## Where this sits

<!-- graph:begin -->
**Stage:** `extract` · **Level:** intermediate · **~35 min**

**You need first:** [Precision and Recall on the Write Path](../extraction-quality/index.md)

**Concepts assumed:** [Atomicity](../../../concepts/atomic-fact.md) · [The Extraction Pipeline](../../../concepts/extraction-pipeline.md) · [Procedural Memory](../../../concepts/procedural-memory.md)
<!-- graph:end -->

## The problem

Three lessons from now you will retire a belief by setting `invalid_at` on a record. That operation works on a whole record, which means the grain chosen at write time decides what can be updated later.

Consider a plausible extraction of session 7:

```
"Priya eats fish, and she does not eat meat, but avoids gluten"
```

Every clause is true. Now Priya starts eating meat again. You cannot retire a third of a record, so the only options are destroying all three facts and re-extracting from a turn you may no longer have, or leaving a memory that is two-thirds correct and one-third false. **Both are data loss**, and neither is visible until the update arrives, months later.

Atomicity is not a style preference. It is the property that makes belief updating possible at all.

## Why this isn't RAG

Chunking optimises for *retrievability* — enough surrounding context that a passage makes sense alone, small enough to rank precisely. Overlapping chunks are normal and harmless, because nobody updates a chunk.

Atomising optimises for *updatability*, which pulls the other way. The unit is "one thing that could independently become false", and duplication across records is a bug rather than a feature, because two copies of a fact means retiring one and leaving the other. The two operations look similar and are solving opposite problems.

## Mechanism

Split on conjunctions that join independent claims, and **stop there**.

```python
SPLIT = re.compile(r",\s+and\s+(?=(?:she|he|they|priya)\b)", re.I)
```

Deliberately narrow. Over-splitting is as damaging as under-splitting and considerably harder to notice: a wrong split produces fragments that each look like a reasonable memory, and nothing downstream can detect that they were once one claim. The lookahead requiring a subject pronoun is what stops it firing inside *"pull the metrics, and diff against last week"*.

**Procedures are exempt, by type.** `atomise` returns procedural content untouched:

```
Priya's weekly report process: pull pipeline metrics from the warehouse,
diff against last week, flag anything over 15% drift, write it up — in that order
```

Split that into four atomic steps and each becomes independently retrievable and collectively useless. Order is load-bearing, and Priya says so explicitly in session 6: *"The diff step matters most. If you skip it the numbers look fine and they aren't."* The 171-character record is the longest memory in the store and it is correctly indivisible.

When updatability and usability conflict, **usability wins** — and the type is what encodes that, which is why the exemption is `if memory_type is PROCEDURAL` rather than a length heuristic.

### Measured

Across the 38 intermediate memories: **0 are non-atomic**. Both procedures return `atomise → 1`, and no semantic fact contains an unsplit conjunction. The stage is doing nothing on this corpus — which is the correct outcome and worth stating, because a transform that never fires is easy to mistake for one that works.

## Design decisions

**Split with rules or with the model?** Rules. The model already had its chance at the candidate stage; asking again is a second call, and clause splitting is a mechanical judgement where a deterministic regex is auditable and free. It also keeps the write path at one model call per turn.

**Why so conservative?** Because the two errors are not symmetric. An under-split record is visibly compound and fixable when you notice. An over-split pair looks like two healthy memories and silently loses the relationship between them — and nothing downstream can reconstruct it.

**Should atomicity be enforced, or measured?** Measured. `is_atomic` reports; nothing rejects a compound memory. A hard rule would have to reject the procedure, and a rule with an exception this important is better expressed as a metric you watch.

## Lab

**You'll implement:** `atomise` with the procedural exemption, and `audit_atomicity` over the store.

**Run:**
```
uv run python curriculum/intermediate/atomic-memories/lab/lab.py
```

**Expected output:** the corpus audits clean at **0 of 38 non-atomic**. Then the constructed cases: a three-clause diet memory splits into three, and the 171-character procedure — the longest record in the store — correctly stays whole.

**Stretch:** the lookahead and the type exemption overlap on purpose — `"pull metrics, and diff against last week"` survives even typed as semantic, because the clause after *and* has no subject. Construct a procedure phrased *with* one (`"Priya pulls the metrics, and she diffs against last week"`) and confirm only the type exemption saves it. Two independent guards, and the corpus happens to exercise the weaker one.

## What this adds to the capstone

`memlab.extract.atomise` — `atomise`, `is_atomic`, wired into the pipeline's second stage.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Retiring one fact destroys two others | Compound record; grain too coarse | Try to supersede half a memory | Atomise at write time |
| Workflow steps come back shuffled | A procedure was atomised | Ask the system to perform a taught procedure | Exempt by type |
| Facts lose their relationship | Over-splitting; conjunction rule too broad | Look for fragments that only make sense together | Narrow the rule; require a subject |
| Atomicity check always passes | The transform never fires | Assert it splits a known compound case | Test the transform, not just the corpus |

## Check yourself

??? question "The 171-character procedure violates atomicity. Why is that correct?"
    Because atomicity serves updatability, and splitting this record does not make it more updatable — it makes it unusable. The steps are not independently meaningful, and their order carries information Priya stated explicitly. A rule applied past its purpose is just a rule.

??? question "Nothing in the corpus is non-atomic. Is the stage pulling its weight?"
    On this corpus it does nothing, and that is worth knowing rather than assuming. Its value is on inputs you have not seen — which is why the lab tests it against constructed compound cases rather than only auditing the store. A transform verified only on data where it never fires is untested.

??? question "Why is over-splitting worse than under-splitting?"
    Because it is silent. A compound record announces itself the moment you try to update half of it. Two over-split fragments each look like a healthy memory, the relationship between them is gone, and nothing downstream can tell they were ever one claim.

## Connections

<!-- graph:begin -->
**Stage:** `extract` · **Level:** intermediate · **~35 min**

**You need first:** [Precision and Recall on the Write Path](../extraction-quality/index.md)

**Concepts assumed:** [Atomicity](../../../concepts/atomic-fact.md) · [The Extraction Pipeline](../../../concepts/extraction-pipeline.md) · [Procedural Memory](../../../concepts/procedural-memory.md)
<!-- graph:end -->
