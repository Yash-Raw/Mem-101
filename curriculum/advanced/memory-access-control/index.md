---
id: memory-access-control
title: "Memory Access Control"
level: advanced
stage: govern
estimated_minutes: 50
concepts_taught: [write-authorisation, leak-assertion]
concepts_required: [memory-topology, competence, retrieval-scoping]
lessons_required: [cross-agent-write-conflicts]
capstone_piece: memlab.agents.authorise
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Memory Access Control

> **In one line.** `leak_check` cannot catch a leak — it can only catch a bug in the thing that prevents leaks, which is why its value is entirely in the day it stops returning zero.

## Where this sits

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~50 min**

**You need first:** [Cross-Agent Write Conflicts](../cross-agent-write-conflicts/index.md)

**Concepts assumed:** [Memory Topology](../../../concepts/memory-topology.md) · [Competence](../../../concepts/competence.md) · [Retrieval Scoping](../../../concepts/retrieval-scoping.md)
<!-- graph:end -->

## The problem

`scopes-and-namespaces` built `Namespace`, `visible`, `partition` and `leak_check` two levels ago and argued that scope is a correctness boundary. Then nothing in `memlab/` imported them. The read path filters with `Scope.matches` instead — a second predicate for the same question.

Measured, the two agree on every probe: **read isolation is enforced.** The taught module and the shipped one arrived at the same answer by different routes, which is luck rather than design, but the boundary holds.

The write side has no equivalent at all. A low-trust agent can file a memory under `Scope(user="priya")` — the user's own namespace, no agent — and nothing objects. It is not a leak: `leak_check` correctly ignores it, because that function catches cross-*user* reads and this is an impersonation inside a namespace the reader already trusts.

## Why this isn't RAG

Retrieval access control is a filter on a corpus someone else owns: this user may see these documents. It is enforced at read time because that is the only time it matters — a document nobody may read is harmless in the index.

A memory a writer should not have written is **not harmless in the store**. It participates in consolidation, arbitration, decay and the store's own clock before any reader appears. `cross-agent-write-conflicts` measured one form of that; here is the other, and neither is reachable by a read-time filter.

## Mechanism

**Three refusals, ordered so each is cheap:**

```
the corpus agent writes, in its own namespace   ADMIT
an agent files under the bare user scope        refuse: impersonation
an agent writes into another tenant             refuse: wrong user
an agent writes dated a year ahead              refuse: future dated
the user says something                         ADMIT
```

**`FUTURE_DATED` is the one that is not obviously access control.** `forget.decay.reference_now` is the newest event in the store, so a single record dated ahead re-ages everything else past the `LONG_TERM` threshold:

| | store | eligible | top-2 for *"where do I work?"* |
|---|--:|--:|---|
| no rogue | 37 | 18 | Calico Systems, staff engineer |
| rogue dated inside the corpus | 38 | **18** | Calico Systems, staff engineer |
| rogue dated a year ahead | 38 | **5** | prefers shorter answers, drinks tea |

And the claim is never even *examined*. *"Priya works at Meridian Health"* matches no marker in the `employer` slot, so it is unnameable in exactly the sense `provenance-and-trust` measured — no conflict candidate, no arbitration, live at confidence 0.3, kept out of retrieval only by the tier cap it just moved. **Authorisation is about what a write can do on the way in, not about whether you end up believing it** — and here nothing ever formed an opinion to begin with.

**Skew is a day, not zero.** A write genuinely arriving now is newer than everything in a fixture, and a policy that rejects the present is a policy nobody runs.

**Refusals are returned, not logged and dropped.** A write path that silently discards is indistinguishable from one that never received anything — the same failure `background-job-mechanics` spent a lesson on, in a different stage.

### And the read-side assertion is a tautology

Write a foreign memory straight into the store, bypassing the policy entirely:

```
in the store        True
visible to priya    False
leak_check catches  0
```

Zero, because `leak_check` is *"visible to this reader **and** owned by someone else"*, and `visible` already excluded it. **The two conditions cannot both hold unless `Namespace.admits` is broken.** Break it and the assertion fires:

```
leak_check with the filter intact    0
leak_check with admits() broken      1
   mallory: Mallory's salary is 90k
```

So it is not a detector, it is an **invariant**: an assertion about the filter rather than about the data, whose number is always zero and whose entire value is the day it is not. That is exactly what belongs in CI, and this module puts it there.

## Design decisions

**Why is impersonation a separate refusal from wrong-user?** Because they fail differently. Wrong-user crosses a tenant boundary and every layer downstream would also be wrong. Impersonation stays inside the correct tenant and is *only* wrong about attribution — the memory is about the right person, filed as though the wrong party said it. A single "unauthorised" verdict would hide which happened, and only one of the two is a security incident.

**Why check the clock in an access-control policy?** Because the alternative is a validation stage nobody adds. The damage is real, measured, and available to any writer; putting it beside the other two costs one comparison and means there is a single place where "what may this writer do" is answered.

**Why keep `Scope.matches` rather than replacing it with `visible`?** Because they agree, and a refactor with no behavioural change is a way to move figures by accident across 56 lessons. What lands instead is the assertion — `leak_check` in CI — which is the thing that would catch them diverging later. Consolidating them is a real piece of work with a real risk, and it should be done when there is a reason beyond tidiness.

## Lab

**You'll implement:** `WritePolicy.check` and `admit`.

**Run:**
```
uv run python curriculum/advanced/memory-access-control/lab/lab.py
```

**Expected output:** the five verdicts above, then **1 of 4** admitted from a mixed batch with all three refusals named, then the future-dated table — **18 / 18 / 5** eligible — and `leak_check` returning **0** intact and **1** with `admits` broken.

**Stretch:** set `skew` to zero and re-ingest. Nothing changes, because every corpus write is dated at or before the store's clock — and then try it on a store whose newest event is a minute old. **A threshold that never fires on your fixture is a threshold you have not tested.**

## What this adds to the capstone

`memlab.agents.authorise` — `Refused`, `Decision`, `WritePolicy`, `check`, `admit`. `Pipeline.admit` switches it on at A3 and `ingest` consults it before storing agent writes, so the shipped path is the one these lessons measure. **Module A3 ends here**: a topology that was priced, trust that scores the claim, arbitration that no longer falls through above the line, and a write path that says no.

Every write the corpus actually contains is admitted, so `@A3` is identical to `@A2` and the whole demonstration is in what the policy refuses.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Agent speaks as the user | No write-side attribution check | File under the bare user scope | Refuse impersonation |
| Half the store stops being retrievable | One future-dated write re-ages everything | Compare the eligible pool before and after | Bound the clock skew |
| Writes disappear without trace | Refusals logged and dropped | Compare admitted count to submitted | Return the decisions |
| Leak assertion always passes | It asserts the filter, not the data | Break `admits` deliberately | Test the assertion itself |
| Two predicates for one boundary | Taught module never imported | Grep for who calls it | Assert they agree |

## Check yourself

??? question "`leak_check` returns zero even for a foreign memory written straight into the store. Is it broken?"
    No — it is doing the only thing it can. It reports memories *visible to this reader* that belong to someone else, and `visible` already excluded the foreign record. The two conditions are contradictory unless the filter is wrong, which is precisely the bug it exists to catch. An invariant that can only fire on a defect is not a weak detector; it is a correctly scoped assertion.

??? question "Why does a clock check belong in an authorisation policy?"
    Because the store ages every memory relative to its newest event, so one write dated ahead demotes thirteen others out of retrieval — no belief required. If authorisation only asks "will we believe this?", it has answered a narrower question than the one that matters, and the validation that would catch it lives nowhere.

??? question "Read isolation already held. What did this module actually change?"
    The write side, which had nothing. Read isolation held by coincidence — two predicates written independently that happen to agree — and the module leaves them alone while adding the assertion that would catch them drifting. What is new is that a writer can now be told no, and that the refusal comes back with a reason.

## Connections

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~50 min**

**You need first:** [Cross-Agent Write Conflicts](../cross-agent-write-conflicts/index.md)

**Concepts assumed:** [Memory Topology](../../../concepts/memory-topology.md) · [Competence](../../../concepts/competence.md) · [Retrieval Scoping](../../../concepts/retrieval-scoping.md)
<!-- graph:end -->
