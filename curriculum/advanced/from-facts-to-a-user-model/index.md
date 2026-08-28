---
id: from-facts-to-a-user-model
title: "From Facts to a User Model"
level: advanced
stage: evolve
estimated_minutes: 50
concepts_taught: [user-model, volatility]
concepts_required: [slot, supersession, unnameable-claim]
lessons_required: [memory-access-control]
capstone_piece: memlab.user.model
lab: lab/lab.py
lab_runtime: fake
status: published
---

# From Facts to a User Model

> **In one line.** Five of the six things the system believes about this person have already changed once — and the sixth is stable only because nobody has moved twice.

## Where this sits

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** advanced · **~50 min**

**You need first:** [Memory Access Control](../memory-access-control/index.md)

**Concepts assumed:** [Slot](../../../concepts/slot.md) · [Supersession](../../../concepts/supersession.md) · [Unnameable Claim](../../../concepts/unnameable-claim.md)

**This unlocks:** [Behaviour as Memory](../implicit-signals/index.md)
<!-- graph:end -->

## The problem

The model everyone builds first is *every live semantic memory*: **19 statements** on this corpus. Two things are wrong with it and neither shows up in the count.

```
about someone else (entities set)     2     Samira is a charge nurse
claiming no attribute to key on       6     Priya mostly does pipeline work
```

A model of Priya containing her partner's job is not a smaller error than a stale fact; it is a different kind of thing entirely, and it will be stated in the first person.

Key it on `SLOT` and the model is **6 attributes**, with **6 statements that cannot enter it at all**.

## Why this isn't RAG

There is no user model in retrieval, and the absence is not an oversight — a corpus has no subject to be a model of. Personalisation in a RAG system means filtering or reranking *someone else's documents* by a profile that lives outside the index.

Here the profile **is** the store, assembled from beliefs that were written one turn at a time by several parties, some of which are about other people, and most of which have already been replaced once. The interesting property is not what the model says; it is how much of it is provisional.

## Mechanism

**Six attributes, and five of them are volatile:**

```
beverage         volatile (1)  tea; three coffees a day
commute          stable   (0)  commutes 40 minutes by train
diet             volatile (1)  eats fish; no meat; pescatarian; gluten intolerance
employer         volatile (1)  works at Calico Systems; staff engineer
residence        volatile (1)  lives at 47 Halloway Road, Bristol
response_style   volatile (1)  prefers shorter answers
```

**Volatility is read from the supersession history, not asserted.** An attribute that has been replaced has demonstrated it can change. That is a fact about the record, available for free, and it needs no judgement about which categories of thing "tend to be stable".

Which is just as well, because judgement would have got it wrong. Diet and residence sound durable and both have changed; the one attribute marked stable is `commute` — and it is stable only because she moved house once and has not moved again. **"Stable" here means "not yet observed to change", and a model that reports it as a property of the attribute is overclaiming.**

**Count supersessions only for beliefs about the user.** A partner changing jobs twice is not evidence that the *user's* employer is volatile, and `occupation_other` — the slot with the most churn on this corpus — is entirely about Samira.

### What cannot enter the model

```
Priya mostly does pipeline work
Priya's phone number is 07700 900412
Priya's new flat is bigger
Priya's new role involves more architecture and less firefighting
Priya has a recurring 1:1 every Tuesday 10:00.
Priya declined all Friday meetings since March 2026.
```

Six true, stated facts that describe nothing the system has a name for. Two are the calendar agent's writes — the same `unnameable` set `provenance-and-trust` measured from the trust side, arriving here as a modelling gap.

**They are returned, not dropped.** A model that silently omits a third of what it was built from looks exactly like one with nothing to omit, and the omission is where the next question lives.

One of them is her phone number. **The model happens not to contain PII, and only because PII has no slot** — an accident that A6 will have to turn into a decision.

## Design decisions

**Why not add slots until nothing is unkeyed?** Because `SLOTS` has five callers across three levels now — conflict detection, ranking, scheduling, trust, and this — with measured figures against each. And the goal is wrong anyway: a slot per fact is a list with extra steps. The model earns its keep by being *smaller* than the store, and `unkeyed` is the honest record of that price.

**Why is an attribute a set of beliefs rather than a value?** Because `diet` is four live beliefs that are all true at once — no meat, fish, pescatarian, gluten. Collapsing them to a single value is the composition `reflection-and-insight` measured as strictly worse under a budget, and forcing it here would repeat that at a layer with less information.

**Why `volatile` rather than a rate?** One supersession is not a rate. Five of six attributes have exactly one, so any number derived from it would be noise dressed as a measurement — and the useful distinction, *has this ever been wrong before*, is fully carried by the boolean.

## Lab

**You'll implement:** `build` and `Attribute.volatile`.

**Run:**
```
uv run python curriculum/advanced/from-facts-to-a-user-model/lab/lab.py
```

**Expected output:** **19** naive statements against **6** attributes, **6** unkeyed and **2** third-party; the six attributes with their volatility; and the unkeyed list including the phone number.

**Stretch:** count supersessions across all slots rather than only the user's own. `occupation_other` — Samira's nursing job — has two, more churn than anything about Priya, and it is not in the model at all. **A volatility number computed over the wrong subject is worse than no volatility number.**

## What this adds to the capstone

`memlab.user.model` — `Attribute`, `UserModel`, `build`. Reads `slot_of` from `evolve.conflict` and `entities` from I2's resolution, so the model is a view over existing structure rather than a parallel one. No pipeline stage: assembling a model is a read-side operation, and `applying-the-model` is where it meets a question.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Model states a partner's fact in the first person | Third-party memories included | Check `entities` on every member | Exclude, and report the count |
| Model looks complete | Unkeyed statements dropped silently | Compare model size to source size | Return what did not fit |
| "Stable" attributes turn out not to be | Never-observed-to-change read as durable | Ask how many times it *could* have | Report the observation, not a property |
| Volatility computed over other people | Supersessions counted store-wide | Group by subject before counting | Count the user's own only |
| Model is a list with extra steps | A slot added per fact | Compare attribute count to statement count | Keep the model smaller than the store |

## Check yourself

??? question "Why is `commute` the only stable attribute, and why is that not reassuring?"
    Because she moved house once, which changed the commute once, and nothing has changed it since. The attribute has been observed not to vary across exactly one opportunity. Reporting that as *stable* attaches a durability claim to the attribute when the evidence supports only a claim about the observation window — and every other attribute in the model has already falsified the same intuition.

??? question "Six statements cannot enter the model. Is the slot table too small?"
    It is incomplete, but growing it is not the fix. The model is useful because it is six attributes rather than nineteen statements; a slot per fact reproduces the list. What the six buy is a named gap — including the phone number, which the model excludes for no better reason than that nobody wrote a slot for it.

??? question "Why keep four separate diet beliefs instead of one composite?"
    Because all four are true simultaneously, and `reflection-and-insight` measured that composing them makes the answer strictly worse under a token budget — the packer can drop one of four atoms and cannot drop a quarter of a composite. The model records what is believed; it does not get to make the assembly decision on assembly's behalf.

## Connections

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** advanced · **~50 min**

**You need first:** [Memory Access Control](../memory-access-control/index.md)

**Concepts assumed:** [Slot](../../../concepts/slot.md) · [Supersession](../../../concepts/supersession.md) · [Unnameable Claim](../../../concepts/unnameable-claim.md)

**This unlocks:** [Behaviour as Memory](../implicit-signals/index.md)
<!-- graph:end -->
