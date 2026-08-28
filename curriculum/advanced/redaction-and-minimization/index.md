---
id: redaction-and-minimization
title: "Redaction and Minimization"
level: advanced
stage: govern
estimated_minutes: 45
concepts_taught: [minimisation, redaction]
concepts_required: [personal-data, label-not-permission, element-cost]
lessons_required: [pii-on-the-write-path]
capstone_piece: memlab.privacy.redact
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Redaction and Minimization

> **In one line.** You can throw away the street address entirely, coarsen every other kind, and the exam still passes — only the health *value* is load-bearing.

## Where this sits

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [PII on the Write Path](../pii-on-the-write-path/index.md)

**Concepts assumed:** [Personal Data](../../../concepts/personal-data.md) · [Label, Not Permission](../../../concepts/label-not-permission.md) · [Element Cost](../../../concepts/element-cost.md)

**This unlocks:** [Deletion That Actually Deletes](../deletion-that-actually-deletes/index.md)
<!-- graph:end -->

## The problem

`pii-on-the-write-path` measured that refusing personal data breaks the system. Redaction is the middle option — keep the fact, drop the detail — and the only honest way to choose a level is to measure what each one costs.

```
address
   full       Priya lives at 47 Halloway Road, Bristol
   coarse     Priya lives in Bristol
   tokenised  Priya — <address>

health
   full       Priya was diagnosed with a gluten intolerance last week
   coarse     Priya has a gluten intolerance last week
   tokenised  Priya — <health condition>
```

| level | kinds | exam |
|---|---|---|
| full | all four | True |
| **coarse** | **all four** | **True** |
| coarse | contact only | True |
| coarse | health only | True |
| **tokenised** | **all four** | **False** |
| **tokenised** | **contact only** | **True** |
| tokenised | health only | False |

**Coarsening every kind costs nothing.** Tokenising the contact details — destroying the address and the phone number outright — also costs nothing. The only redaction that breaks anything is tokenising health, because the exam needs the word *gluten*.

## Why this isn't RAG

Minimisation in a retrieval system is a decision about the corpus, made once, by whoever assembled it. You cannot minimise what you did not write, and the index has no opinion — it will happily return whatever the documents contain.

A memory layer writes every record itself, so **minimisation is available at every write and free to choose per record**. That is an advantage and a trap: the choice is available so often that it never gets made deliberately, and the default is to store the sentence exactly as it arrived.

## Mechanism

**Coarsening is per kind, because "less precise" is not one operation.**

| kind | what coarsening throws away |
|---|---|
| address | the street; keeps the city |
| phone | the number; keeps that one exists |
| health | the diagnosis *event*; keeps the condition |
| third_party_health | — no useful middle; falls through to a token |

The health rule is the instructive one. *"Priya was diagnosed with a gluten intolerance last week"* carries a date and a clinical encounter; *"Priya has a gluten intolerance"* carries the dietary constraint. A question about food needs the second and never the first, and the difference is a regex.

**Third-party health has no coarse form**, and that is a finding rather than a gap. *"Sam is a nurse at St. Aubyn's"* coarsened to *"Sam is a nurse"* still identifies a person's occupation and employer; there is no version of it that is useful to Priya's assistant and not a fact about Sam. It falls through to a token, which is the honest answer: keep that something was said, keep nothing of what.

**Redaction changes the id.** `Memory.id` is content-addressed, so a redacted record is a *different* record — correct, and load-bearing, because a full-detail copy and a redacted copy sharing an id is exactly how the original survives a redaction.

### What the table is really saying

Every argument against minimisation is that it might cost something. Here it costs nothing at three of the four kinds, at the most aggressive level available. **The address can simply be destroyed.** The system that knows where she lives is not more useful than the one that does not — measured against the question it is asked, it is identical.

## Design decisions

**Why measure with the exam rather than by counting removed characters?** Because characters removed is a measure of how much you did, not of what it cost. Tokenising the phone number removes eleven digits and changes nothing; tokenising the health fact removes seven and breaks the answer. The only meaningful unit is whether the system still works.

**Why not tokenise everything and accept the loss?** Because the loss is the exam, and the exam is the reason the store exists. The point of measuring per kind is that *"minimise aggressively"* and *"keep what is needed"* are not in conflict here — they disagree about exactly one kind, and it is knowable which.

**Why keep `FULL` as a level at all?** So that the comparison is in the code rather than in a commit message. A redaction policy with no null option cannot be evaluated, and the first question anyone asks about one is *"what does it cost?"*.

## Lab

**You'll implement:** `redact` and `apply`.

**Run:**
```
uv run python curriculum/advanced/redaction-and-minimization/lab/lab.py
```

**Expected output:** each kind at all three levels, then the nine-row table — **coarse/all four True**, **tokenised/all four False**, **tokenised/contact only True**.

**Stretch:** coarsen the health memory and check the id. It changes, because content is the id — so the redacted record does not replace the original unless something explicitly retires it. **A redaction that adds a record instead of replacing one has doubled the data it was meant to reduce.**

## What this adds to the capstone

`memlab.privacy.redact` — `Level`, `redact`, `apply`, and the per-kind coarsening table. Consumes the labels from `privacy.classify` and enforces nothing on its own; choosing a level is a deployment decision this module prices rather than makes.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Redaction breaks answers | Uniform level across all kinds | Run the exam per kind, per level | Choose per kind |
| Full-detail copy survives | Redacted record added, not swapped | Compare ids before and after | Retire the original |
| Third-party data half-hidden | Coarsening applied where none exists | Read the coarse form aloud | Token, not a middle |
| "We minimise" with no evidence | Measured in characters removed | Ask what it cost the answer | Measure with the exam |
| Nothing ever minimised | Choice available at every write, made at none | Check the default level | A null level to compare against |

## Check yourself

??? question "Tokenising the address destroys it entirely and the exam still passes. Why keep the address at all?"
    Because the exam is one question, and *"what's my address?"* is another that this corpus does not ask. What the measurement establishes is that the address is not load-bearing **for the questions being asked** — which is the argument for coarsening it by default and the reason the answer is a per-deployment decision rather than a course-wide one.

??? question "Why does health have a coarse form when third-party health does not?"
    Because there is a version of the health fact that is useful and less revealing — the condition without the diagnosis event. There is no equivalent for *"Sam is a nurse at St. Aubyn's"*: strip the employer and you still have a named person's occupation, and no amount of coarsening makes it a fact about the account holder. When there is no useful middle, the honest form is a token.

??? question "The redacted memory has a different id. Is that a problem?"
    It is the mechanism working. Ids are content-addressed, so changing content produces a new record — which means a redaction must explicitly retire the original, and a policy that only *adds* the redacted form has doubled the data. The id changing is what makes that failure visible instead of silent.

## Connections

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [PII on the Write Path](../pii-on-the-write-path/index.md)

**Concepts assumed:** [Personal Data](../../../concepts/personal-data.md) · [Label, Not Permission](../../../concepts/label-not-permission.md) · [Element Cost](../../../concepts/element-cost.md)

**This unlocks:** [Deletion That Actually Deletes](../deletion-that-actually-deletes/index.md)
<!-- graph:end -->
