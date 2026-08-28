---
id: rtbf-and-auditability
title: "Proving You Forgot"
level: advanced
stage: govern
estimated_minutes: 45
concepts_taught: [deletion-receipt, proof-without-retention]
concepts_required: [cascade-deletion, request-resolution, memory-record]
lessons_required: [deletion-that-actually-deletes]
capstone_piece: memlab.privacy.audit
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Proving You Forgot

> **In one line.** The obvious proof of a deletion is a copy of what you deleted, which is the one thing the request forbade.

## Where this sits

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [Deletion That Actually Deletes](../deletion-that-actually-deletes/index.md)

**Concepts assumed:** [Cascade Deletion](../../../concepts/cascade-deletion.md) · [Request Resolution](../../../concepts/request-resolution.md) · [The Memory Record](../../../concepts/memory-record.md)
<!-- graph:end -->

## The problem

The cascade removed a record from three structures. Now demonstrate it — to the user, to an auditor, to yourself in six months.

Everything that looks like evidence is a re-disclosure. A log line quoting the content is the content. A copy in a "deleted" table is a copy. Even a search to confirm the data is gone needs the data to search for, and **an audit that requires keeping what was erased has not erased it.**

## Why this isn't RAG

An index deletion is provable by rebuilding: drop the document, re-index the corpus, and the absence is verifiable against a source that legitimately still exists. The corpus is the evidence and nobody asked for it to be destroyed.

Here the record *was* the source. There is nothing left to compare against, so the proof has to be constructed at the moment of deletion, out of things that are not the data.

## Mechanism

**The id is the fingerprint, and it has been since Beginner.** `Memory.id` is a truncated SHA-256 of user, type, content and source — built for deduplication, and it turns out to have exactly the property an audit needs:

```
proves the original record   True
proves a different record    False
receipt contains the content False
```

Anyone holding the original can verify the receipt describes it. Anyone else learns a hex string. **A design decision made two levels ago for a completely different reason is what makes proof-without-retention possible** — and it is worth noticing that it was not planned.

**A receipt records everything except what was said:**

```
receipt for ec6117be8ba33512
   kind      : address
   requested : 2026-06-20   deleted: 2026-06-20
   structures: {'primary': 1, 'sqlite': 1, 'vectors': 1, 'derived': 0, 'summaries': 0}
   reached   : ('primary', 'sqlite', 'vectors')
   residue   : 0   complete=True
```

The request's *text* is not a field. Storing what the user said in order to prove you honoured it is the same mistake one level down; a session number and a timestamp locate the turn without reproducing it.

**The re-scan searches by id, not by content.** Searching for the deleted text means holding the deleted text. `residue == 0` is the claim being made, and it is checkable without anyone ever writing the address down again.

**Receipts expire.** A permanent record that a person asked to be forgotten is itself a permanent record about that person:

```
expired after 100 days   False
expired after 366 days   True
```

The retention window is the awkward part of the design and the honest one — it admits that the receipt is data about the user, subject to the same argument as everything else.

## Design decisions

**Why not sign the receipt?** Because a signature proves the receipt was not altered and says nothing about whether the deletion happened, which is the claim under dispute. The id already binds the receipt to a specific record; adding cryptography without adding evidence is the shape of a control that looks stronger than it is.

**Why keep the structure counts including zeroes?** Because *"reached three structures"* and *"walked five and found three"* are different claims, and only the second is auditable. The zeroes are what distinguishes a cascade that ran from one that never found the graph — the argument `temporal-knowledge-graphs` made, arriving where it has legal weight.

**Why is `complete` derived from a re-scan rather than from the cascade's own counts?** Because the cascade reports what it *did*, and the question is what *remains*. A cascade that removed three copies and missed a fourth reports success on its own terms. The re-scan is the only statement about the store rather than about the operation.

## Lab

**You'll implement:** `Receipt.proves`, `rescan`, and `issue`.

**Run:**
```
uv run python curriculum/advanced/rtbf-and-auditability/lab/lab.py
```

**Expected output:** the receipt with its structure counts, **residue 0** and **complete=True**; `proves` returning **True** for the original and **False** for another record; the receipt containing none of the content; and expiry **False** at 100 days, **True** at 366.

**Stretch:** add the deleted content to the receipt so the proof is legible to a human reading it. Every test still passes, the audit is now much easier to review, and the store contains the address again — in a record specifically kept forever. **The most reviewable audit trail is the one that recreates what it audits.**

## What this adds to the capstone

`memlab.privacy.audit` — `Receipt`, `RETENTION`, `issue`, `rescan`. Depends on nothing but the content-addressed id the record has carried since `the-memory-record`.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Audit trail re-discloses the data | Content copied into the log | Grep the receipts for the deleted value | Fingerprint, not content |
| Verification needs the deleted text | Re-scan searches by content | Ask what the check holds in memory | Scan by id |
| "Deleted" table retains everything | Proof modelled as a copy | Look for what the table stores | Receipts, not copies |
| Forgetting is permanently recorded | Receipts never expire | Ask how long the record lives | A retention window |
| Success reported, copies remain | Completeness taken from the cascade | Re-scan after, independently | Derive from what remains |

## Check yourself

??? question "Why is the id enough to prove a deletion, when it is only sixteen hex characters?"
    Because the claim is narrow. The receipt does not assert what the record said; it asserts *this record*, and anyone with the original can hash it and check. Someone without the original learns nothing, which is the point — proof and disclosure are usually the same operation, and a content-addressed id is one of the few places they come apart.

??? question "The cascade already counted what it removed. Why re-scan?"
    Because those counts describe the operation, not the store. A cascade that reaches three structures and does not know about a fourth reports complete success truthfully. The re-scan is the only statement about what remains, and it is the one an auditor is actually asking for.

??? question "Why should a deletion receipt expire?"
    Because it is a durable record that a specific person asked to be forgotten, which is information about them that they did not volunteer. Keeping it forever to prove you honour deletion requests means never honouring one completely. The window is a compromise and the lesson is that it has to be chosen rather than defaulted to *forever*.

## Connections

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [Deletion That Actually Deletes](../deletion-that-actually-deletes/index.md)

**Concepts assumed:** [Cascade Deletion](../../../concepts/cascade-deletion.md) · [Request Resolution](../../../concepts/request-resolution.md) · [The Memory Record](../../../concepts/memory-record.md)
<!-- graph:end -->
