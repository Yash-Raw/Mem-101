---
id: retrieving-procedures
title: "Retrieving Procedures"
level: advanced
stage: retrieve
estimated_minutes: 45
concepts_taught: [procedural-retrieval]
concepts_required: [procedural-memory, temporal-routing, element-cost]
lessons_required: [learning-from-outcomes]
capstone_piece: memlab.procedural.retrieve
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Retrieving Procedures

> **In one line.** *"How do I do the weekly report?"* retrieves no procedure at all, and the phrasing that retrieves something returns the footnote instead of the recipe.

## Where this sits

<!-- graph:begin -->
**Stage:** `retrieve` · **Level:** advanced · **~45 min**

**You need first:** [Learning From Outcomes](../learning-from-outcomes/index.md)

**Concepts assumed:** [Procedural Memory](../../../concepts/procedural-memory.md) · [Temporal Routing](../../../concepts/temporal-routing.md) · [Element Cost](../../../concepts/element-cost.md)
<!-- graph:end -->

## The problem

The procedure is in the store, live, long-term, and correctly ordered. Ask for it:

```
question                                    procedural?   fact-path rank
how do I do the weekly report?                     True             None
what are the steps for the weekly report           True                1
```

**Absent, not ranked low.** And the one that does return something returns *"In Priya's weekly report, the diff step matters most"* — the annotation A5.1 had to exclude from being a procedure at all — ahead of the four-step recipe.

`gold.yml` predicted this in writing: *"stored as prose and retrieved by similarity, the steps come back shuffled."* Measurement is sharper. They do not come back.

## Why this isn't RAG

Retrieval assumes every unit competes on the same terms, and that assumption is fine for documents, which are roughly interchangeable in kind. A memory store holds facts and workflows in one place, and they are not interchangeable: a fact is a short assertion, a procedure is a long sequence, and **length is a penalty on every similarity metric anyone ships**.

So a procedure loses to a sentence about it, on a question that could only have been asking for the procedure. No amount of tuning the ranker fixes a pool that should not have contained both.

## Mechanism

Three things are wrong, and only one of them is scoring.

**Index.** A procedure is one long memory competing with short ones on a metric that rewards brevity. Restricted to procedures, length stops being a penalty — and the annotation is not a candidate, because A5.1 already established it is not a procedure.

**Trigger.** *"How do I…"* is a request to **act**, not to recall. It is recognised before retrieval, the same shape `temporal-questions` used for *"when did I…"* — and deliberately narrow, so that *"what did I say about the Spark job?"* stays a recall question that happens to mention work:

```
where do I work?                       procedural? False
what did I say about the Spark job?    procedural? False
```

**Injection.** A recipe goes in whole:

```
1. pull pipeline metrics from the warehouse
2. diff against last week
3. flag anything over 15% drift
4. write it up in the shared doc
(step 2 matters most)
```

Numbered, because the order is the content. `slot-value` measured that dropping memories is what makes a tight budget survivable — the packer keeps three of four diet facts and the answer stays right. **This is the memory type where that is not allowed.** Drop the fourth step to save four tokens and the result is not a shorter procedure, it is a wrong one.

The warning is attached because A5.2 bound it while both halves were in hand. Without that, the workflow renders and the reason the second step matters does not.

## Design decisions

**Why a separate index rather than a boost?** Because a boost is a number someone has to tune, and it has to be large enough to overcome a length penalty that varies with the procedure. The question is categorical — this asks how to act — so the answer is a different pool, not a different weight on the same one.

**Why is `is_procedural` narrow?** Because a false positive routes a recall question into a pool of one or two procedures and returns nothing useful, while the fact path that would have answered it never runs. The cost is asymmetric in the same direction `implicit-signals` found: precision protects the case that was already working.

**Why not merge this into `temporal_search`?** They are the same shape — classify, then choose a pool — and they are different classifications over different axes. Merging them means one router with two unrelated responsibilities, and the first question that is both temporal and procedural (*"how did I use to do the report?"*) needs them composed rather than conflated. This corpus has no such question, which is why the composition is not built.

## Lab

**You'll implement:** `is_procedural`, `search`, and `render`.

**Run:**
```
uv run python curriculum/advanced/retrieving-procedures/lab/lab.py
```

**Expected output:** the routing table — procedural **True** for the two how-questions and **False** for the two recall questions — the fact path returning **None** and the annotation at rank **1**, the procedural path returning one workflow for both, and the rendered four steps with *(step 2 matters most)*.

**Stretch:** widen `is_procedural` to any question containing *"what"*. *"What should I not eat?"* routes to the procedural pool, finds nothing, and the diet facts are never retrieved. **A router that is wrong about the question makes the correct index unreachable.**

## What this adds to the capstone

`memlab.procedural.retrieve` — `ProceduralHit`, `is_procedural`, `search`, `render`. **Module A5 ends here**: a procedure whose order survives extraction, a lesson whose consequence does not, and a read path that finds workflows because it stopped asking them to compete with facts.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Procedure never retrieved | Long memory competing with short facts | Ask for it directly; check the rank | A separate index |
| Footnote returned instead of recipe | Annotation in the same pool | Look at what rank 1 actually is | Exclude non-procedures |
| Steps arrive incomplete | Packer dropped one to fit a budget | Count steps in the rendered output | Inject whole or not at all |
| Recall question finds nothing | Router too broad | Route a fact question and see | Narrow the trigger |
| Warning missing from the workflow | Annotation never bound | Render and look for the critical step | Bind at write time |

## Check yourself

??? question "The procedure is live, long-term and correctly ordered, and it is not in the top five. What is broken?"
    The pool. It is a long memory scored against short ones by a metric that rewards brevity, so it loses to a one-line comment about itself. Nothing in the ranker is malfunctioning — it is answering a question about similarity correctly, and similarity was the wrong question to ask about a workflow.

??? question "Why can a procedure not be trimmed to fit a budget?"
    Because a procedure with three of its four steps is not a partial answer, it is a wrong one, and it looks exactly like a complete one. Every other memory type in this course degrades gracefully under a budget — three of four diet facts still answers the question. This one degrades into something a person might follow.

??? question "`is_procedural` and `temporal-questions`' classifier are the same shape. Why keep them apart?"
    Because they classify different axes, and merging gives one router two responsibilities with no shared logic. The moment that matters is a question that is both — *"how did I use to do the report?"* — which needs the two composed, temporal filter feeding the procedural pool. This corpus contains no such question, so the composition is described and not built.

## Connections

<!-- graph:begin -->
**Stage:** `retrieve` · **Level:** advanced · **~45 min**

**You need first:** [Learning From Outcomes](../learning-from-outcomes/index.md)

**Concepts assumed:** [Procedural Memory](../../../concepts/procedural-memory.md) · [Temporal Routing](../../../concepts/temporal-routing.md) · [Element Cost](../../../concepts/element-cost.md)
<!-- graph:end -->
