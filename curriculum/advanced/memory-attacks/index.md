---
id: memory-attacks
title: "Memory Attacks"
level: advanced
stage: govern
estimated_minutes: 50
concepts_taught: [threat-model, accidental-control]
concepts_required: [cascade-deletion, write-authorisation, competence]
lessons_required: [rtbf-and-auditability]
capstone_piece: memlab.privacy.attacks
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Memory Attacks

> **In one line.** Three of the four attacks are already defended, all three defences were built for something else, and the fourth leaves the deleted address's timestamp in four other records.

## Where this sits

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~50 min**

**You need first:** [Proving You Forgot](../rtbf-and-auditability/index.md)

**Concepts assumed:** [Cascade Deletion](../../../concepts/cascade-deletion.md) · [Write Authorisation](../../../concepts/write-authorisation.md) · [Competence](../../../concepts/competence.md)

**This unlocks:** [Why Memory Eval Is Hard](../why-memory-eval-is-hard/index.md)
<!-- graph:end -->

## The problem

Four ways to attack a memory layer, and the state of the system against each:

| attack | covered | defence |
|---|---|---|
| poisoning | **True** | claim-scoped trust into arbitration (A3.3) |
| injection | **True** | the durability gate routes imperatives away (I1) |
| cross-user read | **True** | scope filter, plus `leak_check` as an invariant (A3.4) |
| **extraction** | **False** | none |

Exercised against the live store:

```
injection : imperatives in the store    0
cross-user: leak_check(priya)           0
poisoning : impersonating write refused True
```

Three for three. And **all three defences were built for something other than security** — arbitration to decide between two honest beliefs, the gate to keep requests out of the belief store, scopes because ranking across tenants returns noise.

## Why this isn't RAG

A retrieval corpus is written by people who are not attacking you, curated before it is indexed, and identical for every reader. Prompt injection targets the *model*, and the standard mitigation is to treat retrieved text as data — which works because the text was never going to be believed as a fact about the user.

A memory layer's corpus is written **by the adversary**, one turn at a time, and every record is a first-person claim about the person whose questions it will answer. There is no curation step to defend, and "treat it as data" is not available: believing it is the entire function.

## Mechanism

**The defences are accidental, and that is the finding.**

```
accidental: 3 of 3 defences built for another reason
```

A control that exists as a side effect is a control nobody maintains **as a control**. It will be refactored for the reason it was built, by someone who does not know it is load-bearing twice — and every one of these has a stated residual that a maintainer working on the original purpose would have no reason to preserve:

| attack | what still gets through |
|---|---|
| poisoning | only claims naming a modelled slot are arbitrated at all; an unnameable one is never compared |
| injection | the gate matches two phrasings; a request worded as a fact is stored as one |
| cross-user | the assertion fires only if the filter itself is broken |

The poisoning residual is the one to sit with. `provenance-and-trust` measured that **2 of 3 agent writes claim no slot** and are therefore never arbitrated. The defence covers exactly the writes that happen to be contestable.

### Extraction, which nothing covers

Delete the address and look at what carries its exact instant:

```
the deleted record: Priya lives at 47 Halloway Road, Bristol
   its happened_at: 2025-08-02 11:15:00+00:00

what survives carrying that instant:
   happened_at  Priya moved house
   happened_at  Priya's phone number is 07700 900412
   valid_from   Priya used to cycle to work before the move
   valid_to     Priya's colleague mentioned she is relocating to Berlin.

   derived_from pointing at it: 0
```

**Four records, and the cascade had nothing to follow.** The `valid_from` on the cycling memory is the sharpest: A1's parser resolved *"before the move"* by looking up the address memory's timestamp and writing it into another record — an information flow that created no `derived_from` edge, because nothing asked it to.

None of this recovers the street name. It recovers that a move happened on 2025-08-02, which is the fact the deletion was arguably about, and it is a *lower bound* on the residue rather than an inventory: these are the flows visible from one field.

## Design decisions

**Why is nothing built here?** Because the honest deliverable is the survey. Three defences exist and need documenting *as* defences so they survive refactoring; the fourth needs a mechanism this module does not have — tracking derivation through timestamps means `derived_from` on every field a parser reads, which is a write-path change with its own measurement. Building a partial one would produce a control that reports success.

**Why classify the defences by what they were built for?** Because that predicts how they will be lost. `leak_check` will be deleted by someone tidying an assertion that always passes. The gate's imperative list will be narrowed by someone fixing a false positive. Naming the second purpose in the code is the cheapest available protection.

**Why does the corpus have no attacker?** Because it has one, and it is the travel agent — a low-trust writer whose one contribution is an unconfirmed claim that contradicts a first-party fact. That is a poisoning attempt as it actually arrives: not malicious, just wrong and confident, which is the shape the defence has to handle either way.

## Lab

**You'll implement:** `survey`, `uncovered`, and `accidental`.

**Run:**
```
uv run python curriculum/advanced/memory-attacks/lab/lab.py
```

**Expected output:** the four-row table with **extraction** uncovered, **3 of 3** defences accidental, the three live checks passing, and the four records carrying the deleted timestamp with **0** `derived_from` edges to follow.

**Stretch:** delete the phone number as well, then re-run the timestamp scan. It shares `happened_at` with the address — same turn — so deleting either leaves the other pointing at the same instant. **Two records deleted for the same reason still reconstruct each other's existence.**

## What this adds to the capstone

`memlab.privacy.attacks` — `Attack`, `Defence`, `survey`, `uncovered`, `accidental`. **Module A6 ends here**: personal data labelled, minimisation priced, deletion that reaches every structure, proof that retains nothing, and a written record of which controls are load-bearing by accident.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| A control disappears in a refactor | Built for another purpose, undocumented | Ask why each defence exists | Name the second purpose |
| Poisoning succeeds via an odd phrasing | Only slot-naming claims are arbitrated | Count unnameable agent writes | Flag the unchecked |
| A request stored as a fact | Gate matches phrasings, not intent | Word an instruction as a statement | Widen with care |
| Deleted values inferred from metadata | Timestamps propagate without edges | Scan for the deleted record's instants | Track derivation through fields |
| "Secure" with no threat model | Defences never enumerated | Write the four down and check each | This survey |

## Check yourself

??? question "Three attacks are covered. Why is that not reassuring?"
    Because none of the three defences was built to defend anything. Arbitration decides between honest beliefs, the gate keeps requests out of the belief store, scopes stop cross-tenant ranking returning noise — and each will be maintained by someone pursuing that purpose, who has no reason to preserve the security property. A control nobody knows is a control is a control with a maintenance plan that does not mention it.

??? question "Deleting the address leaves four records carrying its timestamp. Is the deletion still valid?"
    The record is gone from every structure and the receipt is honest about what it removed. What survives is not the address but the *event* — that a move happened on a specific day — inferable from a field the cascade never looks at, because `derived_from` records derivation between memories and A1's parser wrote a timestamp across records without creating an edge. The deletion is complete against its own definition, and the definition is narrower than the request.

??? question "Why enumerate the attacks rather than build a defence for extraction?"
    Because the mechanism is a write-path change — recording derivation through every field a parser reads — with its own cost and its own measurement, and a partial version would be worse than none: a cascade that follows some timestamp flows reports success while missing others. The survey's value is that `extraction: False` is now a fact in the codebase rather than an absence nobody wrote down.

## Connections

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~50 min**

**You need first:** [Proving You Forgot](../rtbf-and-auditability/index.md)

**Concepts assumed:** [Cascade Deletion](../../../concepts/cascade-deletion.md) · [Write Authorisation](../../../concepts/write-authorisation.md) · [Competence](../../../concepts/competence.md)

**This unlocks:** [Why Memory Eval Is Hard](../why-memory-eval-is-hard/index.md)
<!-- graph:end -->
