---
id: learning-from-outcomes
title: "Learning From Outcomes"
level: advanced
stage: evolve
estimated_minutes: 45
concepts_taught: [lessons-learned, dropped-clause]
concepts_required: [procedural-memory, step-order, extraction-pipeline]
lessons_required: [procedural-memory]
capstone_piece: memlab.procedural.outcomes
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Learning From Outcomes

> **In one line.** The user explained exactly once why a step matters, and extraction kept the conclusion and dropped the evidence.

## Where this sits

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** advanced · **~45 min**

**You need first:** [Procedural Memory](../procedural-memory/index.md)

**Concepts assumed:** [Procedural Memory](../../../concepts/procedural-memory.md) · [Step Order](../../../concepts/step-order.md) · [The Extraction Pipeline](../../../concepts/extraction-pipeline.md)
<!-- graph:end -->

## The problem

Session 6, second turn — two sentences:

```
The diff step matters most. If you skip it the numbers look fine and they aren't.
```

A claim about importance, and the consequence that justifies it. One memory comes out:

```
In Priya's weekly report, the diff step matters most
```

Search the store for the other half:

```
'numbers look fine' anywhere in the store   NO
'skip'                                      NO
```

The store believes the diff step matters and holds **no record of why**. That is the difference between a preference and a checkable claim: asked *"why does the diff step matter?"* the store has nothing, and the transcript has the whole answer.

## Why this isn't RAG

A retrieval corpus never loses the justification, because it never separates it from the claim. Both sentences live in the same document, three words apart, and any passage that surfaces one surfaces the other.

A memory layer extracts *assertions*, and a conditional is not an assertion — *"if you skip it the numbers look fine"* is not a fact about the world, it is a fact about a counterfactual. An extractor tuned to produce durable statements will drop it every time, and the thing it drops is the only part that could ever be argued with.

## Mechanism

**A lesson is a triple:** trigger, consequence, and the step it warns about.

```
trigger      'it'
consequence  "the numbers look fine and they aren't"
step         'diff against last week'   attached=True
in the store  False
```

**Extraction runs over the transcript, not the store.** Not a convenience — a necessity. Once the write path drops a clause, no amount of reading the store recovers it, and a lessons-learned feature built on the store would find nothing and conclude the user never explained anything.

**The pronoun does the damage.** *"If you skip **it**"* refers to whatever the previous sentence named — a different sentence, and after extraction a different memory. Resolving it needs the annotation still in hand, so the binding is only possible while both halves are together. Ten minutes later there is no *it* to resolve.

### One lesson, in a corpus of twenty-four turns

That is the honest count, and it is not because nothing went wrong. It is because people state consequences rarely and conditionally, and the one time this user did, the shape they used was the shape the extractor discards.

The right conclusion is not *"build a lessons-learned store"* — one row does not need a store. It is that **the write path is where this is won or lost**, and the measurement says it is currently lost.

## Design decisions

**Why not change the extractor now?** Because the fixtures producing these memories are authored, and changing them moves a store shape that fifty-nine lessons quote figures against. What lands instead is the measurement and the structure, so the change has a test to satisfy when it happens. `procedural-memory` deferred the same decision for the same reason, and the two together are the argument for making it once.

**Why a conditional pattern rather than a model call?** Because the failure mode of a classifier here is inventing a consequence that was never stated, attached to a step, presented as something the user said. Four regexes that find one real lesson beat a model that finds three and fabricates one — the same argument `implicit-signals` made about corrections, in the module where the fabricated item would be an instruction.

**Why keep `trigger` when it is usually a pronoun?** Because it records *what the binding had to resolve*. A lesson whose trigger is `'it'` is one that could only be attached in the moment; a lesson whose trigger names its step can be attached at any time. That distinction is the difference between a signal you must catch and one you can process later.

## Lab

**You'll implement:** `extract`, `attach`, and `recorded`.

**Run:**
```
uv run python curriculum/advanced/learning-from-outcomes/lab/lab.py
```

**Expected output:** **1** lesson stated in the corpus, its trigger `'it'`, its consequence *"the numbers look fine and they aren't"*, attached to `'diff against last week'`, and **not in the store**.

**Stretch:** run `extract` over the memories instead of the transcript. It returns nothing, and every assertion about attachment still passes because there is nothing to attach. **A feature that reads only the store cannot discover that the store is missing something.**

## What this adds to the capstone

`memlab.procedural.outcomes` — `Lesson`, `extract`, `attach`, `recorded`. Reads the transcript through `fixtures.load_turns` rather than the store, and binds to `procedural.steps.Procedure` for the step it warns about.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| System asserts a rule it cannot justify | Consequence clause dropped at extraction | Search the store for the justification | Extract conditionals too |
| Lessons-learned store is empty | Built over the store, not the transcript | Compare counts from each source | Read the source |
| Warning attached to the wrong step | Pronoun resolved after the pair was split | Check what `trigger` resolved against | Bind while both halves are held |
| Invented consequences | Model asked to generalise from outcomes | Check each against a stated sentence | Patterns, not classification |
| Built a store for one row | Volume assumed rather than counted | Count lessons in the corpus | Fix the write path instead |

## Check yourself

??? question "The store kept "the diff step matters most" and dropped the reason. Which is the more useful half?"
    The reason, and it is not close. The conclusion is an instruction the system can only repeat; the consequence is a claim it can act on, explain, and be wrong about. *"If you skip it the numbers look fine and they aren't"* tells you the failure is silent, which is why the step matters — and none of that is recoverable from *"it matters most"*.

??? question "Why extract from the transcript when everything else in this course reads the store?"
    Because the store is the thing under examination. A lessons-learned feature reading the store would find zero lessons and report that the user never explains their reasoning, when the truth is that they explained it once and the write path discarded it. The only way to measure what extraction dropped is to look at what it was given.

??? question "One lesson in twenty-four turns. Is this module worth having?"
    The structure is; the store is not. One row does not justify a lessons-learned store, and building one would be the mistake this course keeps naming — machinery for a case the data does not contain. What the count justifies is a change to the write path, and the measurement is what makes that change arguable rather than a preference.

## Connections

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** advanced · **~45 min**

**You need first:** [Procedural Memory](../procedural-memory/index.md)

**Concepts assumed:** [Procedural Memory](../../../concepts/procedural-memory.md) · [Step Order](../../../concepts/step-order.md) · [The Extraction Pipeline](../../../concepts/extraction-pipeline.md)
<!-- graph:end -->
