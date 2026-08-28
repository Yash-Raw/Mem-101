---
id: cold-start-and-shared-accounts
title: "Cold Start and Shared Accounts"
level: advanced
stage: retrieve
estimated_minutes: 45
concepts_taught: [coverage-vs-knowledge]
concepts_required: [user-model, entity-resolution, disclosure]
lessons_required: [applying-the-model]
capstone_piece: memlab.user.coverage
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Cold Start and Shared Accounts

> **In one line.** The model was complete at turn 20 and still could not answer the question until turn 22 — a readiness check that counts attributes reports green before the answer exists.

## Where this sits

<!-- graph:begin -->
**Stage:** `retrieve` · **Level:** advanced · **~45 min**

**You need first:** [Personalization Without Creepiness](../applying-the-model/index.md)

**Concepts assumed:** [User Model](../../../concepts/user-model.md) · [Entity Resolution](../../../concepts/entity-resolution.md) · [Disclosure](../../../concepts/disclosure.md)

**This unlocks:** [Procedural Memory](../procedural-memory/index.md)
<!-- graph:end -->

## The problem

Cold start is usually framed as *"we know nothing yet"*. Measured, the model fills faster than that suggests and the interesting property is a different one:

```
turn  1   2 memories  1 attribute   employer
turn  3   5 memories  3 attributes  diet, employer, response_style
turn  8  11 memories  4 attributes  + beverage
turn 12  18 memories  5 attributes  + residence
turn 20  31 memories  6 attributes  + commute
turn 24  34 memories  6 attributes
```

**Half the model exists after three turns.** The last attribute takes twenty. And:

```
first attribute the question reaches   turn 1
model complete (6 of 6 attributes)     turn 20
first turn it answers the exam fully   turn 22
```

For two turns the model had every attribute it would ever have, while a fact the answer needs — the gluten intolerance, arriving in session 12 — was still missing. **Attribute coverage is not knowledge**, and a readiness gate counting attributes is optimistic in exactly the window where being wrong is most likely.

## Why this isn't RAG

A retrieval system has no cold start worth the name. Point it at a corpus and it is as good on day one as it will ever be, because the corpus was written before you arrived. Sparsity is a property of the collection, not of the relationship.

A memory layer starts empty for every user, fills at the rate they talk, and — this is the part with no analogue — may be filling with **more than one person's facts** through a single account. A shared corpus is normal. A shared *subject* is a bug.

## Mechanism

**Report coverage as attributes, and answerability separately.** `growth` counts what the model has; `answerable` reads what those attributes contain. Two milestones, two turns apart on this corpus, and the cheap one is the one that lies.

**Partial models are usable from turn one.** The question reaches `employer` immediately, and `applying-the-model`'s split means an incomplete model degrades by *answering less*, not by answering wrongly — the attributes it does not have are simply not in the `asked` set. That is a property of keying on slots, and it is why cold start needs no special-casing here.

### The shared account is already in the corpus

Two people appear in this store, and the only thing keeping the second out of the first's model is the `entities` field I2 populates. Turn it off:

```
entities intact     6 attributes
entities stripped   7 attributes
   [occupation_other] Samira is a charge nurse
   [occupation_other] Sam still works nights
```

A model of Priya that says she is a charge nurse who works nights. That is her partner, and it is stated in the first person to anyone who asks what she does.

**This is entity resolution's bill, arriving two levels after it was paid.** I2 measured it as a retrieval problem — evidence about one person split across records that never meet. Here the same mechanism is the only thing standing between one account and two people's identities merged into one profile.

## Design decisions

**Why not a confidence score on the model?** Because the failure is categorical. The model is not *less sure* about the gluten intolerance at turn 20; it has never heard of it. A number between 0 and 1 invites treating a missing fact as a weakly held one, and the honest report is the attribute list plus what the question needed.

**Why does an incomplete model not need a special mode?** Because `apply` already returns only the attributes a question reaches. A model with three attributes answers the questions those three cover and stays silent on the rest — the same behaviour as a complete model asked about something it does not track. Cold start is the general case, observed early.

**Why not detect shared accounts?** Because the detector already exists and runs on every write: entity resolution. Adding a second, model-layer check would be a second implementation of the same question, and `memory-access-control` measured what that costs — two predicates for one boundary, agreeing by luck. What this module adds is the *measurement* that shows what resolution is buying.

## Lab

**You'll implement:** `growth`, `answerable`, and `merged`.

**Run:**
```
uv run python curriculum/advanced/cold-start-and-shared-accounts/lab/lab.py
```

**Expected output:** the growth curve — **1, 3, 4, 5, 6, 6** attributes at turns 1, 3, 8, 12, 20, 24 — the three milestones at turns **1**, **20** and **22**, and the stripped model gaining `occupation_other` with Samira's two facts.

**Stretch:** run `answerable` at every turn and find the first `True`. It is turn 22, two after the model stops growing — and if you gate a feature on `len(attributes) == 6`, those two turns ship a confident wrong answer. **The metric that is easy to compute is the one that goes green first.**

## What this adds to the capstone

`memlab.user.coverage` — `Coverage`, `growth`, `answerable`, `merged`. **Module A4 ends here**: a model keyed on attributes, corrections read from behaviour, an application split by how each attribute is used, and a measurement of what the model does not yet know.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Confident answer from a complete-looking model | Readiness gated on attribute count | Compare coverage to answerability | Read the contents, not the keys |
| Partner's job reported as the user's | Entity links lost or never made | Build the model with `entities` stripped | Resolution on the write path |
| Cold start special-cased | Assumed a partial model needs a mode | Ask a partial model an uncovered question | Key on slots; silence is free |
| Missing fact treated as uncertain | Confidence score over the model | Ask what a 0.6 model means | Report absence, not doubt |
| Two detectors for one boundary | Model-layer shared-account check added | Ask which one is authoritative | Measure what resolution buys |

## Check yourself

??? question "The model is complete at turn 20 and answers at turn 22. Which number would you report as readiness?"
    Neither alone. Coverage says which attributes exist and is cheap; answerability says whether the facts a question needs are among them and requires the question. The trap is that coverage is computable without knowing what will be asked, so it is the one that gets wired to a feature flag — and it goes green two turns early, in the window where a confident wrong answer is most likely.

??? question "Why does an incomplete model not answer wrongly?"
    Because `apply` returns only the attributes the question reaches, so an attribute the model lacks contributes nothing rather than contributing a guess. A three-attribute model answers three attributes' worth of questions and is silent elsewhere — identical to how a complete model behaves when asked about something it does not track.

??? question "What does turning off `entities` actually demonstrate?"
    What entity resolution has been buying since I2, at a layer two levels above where it was built. It was introduced to stop evidence about one person fragmenting across records; the same field is the only thing preventing a shared account from merging two people's identities into one profile stated in the first person.

## Connections

<!-- graph:begin -->
**Stage:** `retrieve` · **Level:** advanced · **~45 min**

**You need first:** [Personalization Without Creepiness](../applying-the-model/index.md)

**Concepts assumed:** [User Model](../../../concepts/user-model.md) · [Entity Resolution](../../../concepts/entity-resolution.md) · [Disclosure](../../../concepts/disclosure.md)

**This unlocks:** [Procedural Memory](../procedural-memory/index.md)
<!-- graph:end -->
