---
id: latency-budget
title: "The Latency Budget"
level: advanced
stage: govern
estimated_minutes: 45
concepts_taught: [latency-budget, critical-path]
concepts_required: [cost-profile, sleep-time-compute, consistency-window]
lessons_required: [cost-model]
capstone_piece: memlab.cost.latency
lab: lab/lab.py
lab_runtime: fake
status: published
---

# The Latency Budget

> **In one line.** 81% of the per-turn model cost is on the critical path, and it is the stage nobody proposes deferring.

## Where this sits

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [The Write Path Dominates](../cost-model/index.md)

**Concepts assumed:** [Cost Profile](../../../concepts/cost-profile.md) · [Sleep-Time Compute](../../../concepts/sleep-time-compute.md) · [Consistency Window](../../../concepts/consistency-window.md)
<!-- graph:end -->

## The problem

`cost-model` counted 2.0 model calls per turn on the write path. They do not all have the same deadline.

```
extract    synchronous   a memory not extracted cannot be retrieved on the next turn
resolve    synchronous   entity links are needed to file the memory correctly
dedupe     deferred      a duplicate is retrievable; it is just wasteful
arbitrate  synchronous   only on a contested slot -- the A2 gate; otherwise deferred
decay      deferred      salience drifts slowly; a turn's delay is invisible
summarise  deferred      nothing reads a summary that does not exist yet
reflect    deferred      and unwired anyway -- A2.3 measured it as a regression

synchronous stages: 3 of 7
per turn: synchronous 2.0  deferred 0.46  total 2.46
blocking share: 81%
```

**The expensive-sounding stage is the deferrable one.** Consolidation is the pass over the whole store, and the A2 gate already pulls only 11 turns of 24 back onto the critical path — 0.46 calls per turn. Extraction, which is one call per turn and sounds cheap, is the entire blocking cost.

## Why this isn't RAG

A retrieval system's latency budget is spent at read time and the user is watching every millisecond of it: embed, search, rerank, generate. Indexing latency is nearly free to trade away, because nobody is waiting for it.

Here the read path is arithmetic over a cached index and the *write* path is where the model calls are — and the user is waiting for that too, because the next turn will be answered from what this turn stores. **The deadline is not "before the answer", it is "before the next question"**, which is a different and more forgiving budget, and the whole reason deferral is available at all.

## Mechanism

**Ask what breaks if this waits one turn.** Every classification here follows from that question and none of it needs timing:

- A memory not extracted **cannot be retrieved** next turn. Synchronous.
- A duplicate **is** retrievable, just wasteful. Deferred.
- A summary that does not exist yet is not read by anything. Deferred.
- A contested slot answered stale is the eleven-turn window `sleep-time-compute` measured. Synchronous *on those turns only* — which is the gate, priced.

**`arbitrate` is the only conditional entry**, and that is the interesting one. It is not synchronous or deferred by nature; it is synchronous **when the turn contests something**, which is a property of the turn rather than the stage. Every other row is a property of the stage.

**81% blocking, and the honest reading is that there is little left to move.** Extraction is 2.0 of the 2.46 calls, and deferring it is not an optimisation — it is a system that cannot answer a question about the sentence it just heard. The remaining 0.46 is what A2's gate already decided to pay deliberately.

## Design decisions

**Why count calls rather than measure milliseconds?** Same reason as `cost-model`: seconds belong to the provider and the machine, and this corpus runs against a deterministic fake. A model call is the unit that transfers between deployments, and the split between blocking and deferred is a structural property that a stopwatch would only confirm.

**Why is `resolve` synchronous when entity links seem cosmetic?** Because filing is not cosmetic. A memory stored without its entity link is invisible to `cold-start-and-shared-accounts`' third-party exclusion and to `provenance-and-trust`' third-party detection, so the next turn's model is built wrong. It is cheap and it is on the path.

**Why list `reflect` at all when it is unwired?** Because a latency budget that omits the stages you decided not to run is a budget that will silently gain them back. A2.3 measured reflection as a regression and left it in the codebase; the budget records that it would be deferred if it ever returned.

## Lab

**You'll implement:** `split` and `budget`.

**Run:**
```
uv run python curriculum/advanced/latency-budget/lab/lab.py
```

**Expected output:** the seven stages with their classifications, **3 of 7** synchronous, per turn **2.0** synchronous against **0.46** deferred, and an **81%** blocking share.

**Stretch:** classify `extract` as deferred and re-read `sleep-time-compute`'s table. The consistency window stops being 11 turns and becomes every turn, because nothing has been written to be inconsistent about. **A stage you cannot defer is one whose latency you can only reduce, and extraction is the only one in this system.**

## What this adds to the capstone

`memlab.cost.latency` — `When`, `Stage`, `split`, `Budget`, `budget`. Takes its numbers from `cost-model`'s call counts and `sleep-time-compute`'s gate rather than measuring anything new.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Optimising the wrong stage | Cost confused with blocking cost | Split by deadline before optimising | Ask what breaks if it waits |
| Assistant cannot recall the last turn | Extraction deferred | Ask about something just said | Extraction is synchronous |
| Budget silently grows | Unwired stages omitted from it | List every stage, wired or not | Record the decision |
| Gate cost invisible | Conditional stage counted as always-on | Count the turns it fires on | Price it per turn |
| Latency tuned by stopwatch | Measured in a deployment's units | Ask what transfers | Count calls |

## Check yourself

??? question "Consolidation is the pass over the whole store. Why is it not the latency problem?"
    Because nothing reads its output before the next turn unless the turn contested a slot. `sleep-time-compute` measured that: gating on contested slots runs it 11 times in 24 turns, which is 0.46 calls per turn against extraction's 2.0. The expensive stage is the one you can move; the cheap one is the one you cannot.

??? question "What is different about `arbitrate`'s classification?"
    It is the only entry that depends on the *turn* rather than the stage. Extraction is always synchronous and summarisation always deferrable; arbitration is synchronous exactly when the turn claims a slot something live already claims. That is the A2 gate, and this lesson is where its cost is written down as a per-turn number.

??? question "81% of the cost is unavoidable. What is the budget for, then?"
    Knowing that. A latency budget's first job is to say how much room there is, and here the answer is 19% — so effort spent moving work off the turn has a ceiling, and effort spent making extraction cheaper does not. That is a routing decision about engineering time, and it is the opposite of what the stage names suggest.

## Connections

<!-- graph:begin -->
**Stage:** `govern` · **Level:** advanced · **~45 min**

**You need first:** [The Write Path Dominates](../cost-model/index.md)

**Concepts assumed:** [Cost Profile](../../../concepts/cost-profile.md) · [Sleep-Time Compute](../../../concepts/sleep-time-compute.md) · [Consistency Window](../../../concepts/consistency-window.md)
<!-- graph:end -->
