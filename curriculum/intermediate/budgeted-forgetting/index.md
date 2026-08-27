---
id: budgeted-forgetting
title: "Forgetting Under a Budget"
level: intermediate
stage: evolve
estimated_minutes: 40
concepts_taught: [eviction]
concepts_required: [decay-function, salience, supersession]
lessons_required: [decay-and-tiers]
capstone_piece: memlab.forget.budget
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Forgetting Under a Budget

> **In one line.** Tighten the cap by four memories and the system forgets that Priya does not eat meat — eviction is a correctness decision wearing a cost knob's clothes.

## Where this sits

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** intermediate · **~40 min**

**You need first:** [Decay and Memory Tiers](../decay-and-tiers/index.md)

**Concepts assumed:** [Decay](../../../concepts/decay-function.md) · [Salience](../../../concepts/salience.md) · [Supersession](../../../concepts/supersession.md)

**This unlocks:** [Scope, Then Rank](../scope-then-rank/index.md)
<!-- graph:end -->

## The problem

Decay gives every memory a number. Something still has to decide *how many* survive, because decay alone has no notion of capacity — it will happily leave a thousand memories above threshold.

So: a cap, and evict below it. Sweep the cap and watch:

| cap | retrievable | exam answered from the retrievable tier |
|--:|--:|---|
| 20 | 18 | **CORRECT** |
| 16 | 16 | broken — *avoid: gluten only* |
| 12 | 12 | broken — *avoid: gluten only, fish not permitted* |
| 8 | 8 | broken |

At 16, `Priya does not eat meat` is evicted. **The system forgets a dietary restriction**, and reports that Priya should avoid gluten — a confident, fluent, incomplete answer about food, which is the category where incomplete answers matter.

The cap looks like a cost control and behaves like a correctness parameter. Nothing in the code marks the difference.

## Why this isn't RAG

An index has a size limit and evicting from it is genuinely just cost: drop a document and the query returns the next-best passage, slightly worse. The document still exists and can be re-indexed.

Evicting a memory removes the system's **only** record of something true. There is no corpus to rebuild from and no next-best passage — the fact simply stops existing as far as every future question is concerned. That is why the operation has to be demotion rather than deletion, and why the cap deserves the scrutiny a correctness parameter gets rather than the shrug a cache size gets.

## Mechanism

**Cap the retrievable tier, not the store.** The cost is per-query and per-slot, so bounding what retrieval *scans* is what bites. Bounding the log saves storage, which was never the problem.

**Eviction is tier demotion. Nothing is deleted.**

```python
out = [replace(m, tier=Tier.WORKING) if m.id in demoted else m for m in memories]
```

Same discipline as [supersession](../supersession-not-deletion/index.md), different trigger. A superseded belief is *false*; an evicted memory is *still true* and simply stopped earning its slot. The record stays in the log, reachable by an explicit historical query, and recoverable the moment reinforcement lifts it back.

**The cap does not currently bind.** At `@I5` there are **18** retrievable memories against a cap of **20**, so `enforce` evicts nothing. That is worth stating plainly rather than hiding behind a mechanism that appears to be working: the machinery exists ahead of the pressure, because the pressure arrives as a slow degradation rather than an incident, and by the time it is obvious the store is already too big to reason about.

**And summarization stays off.** [Compaction](../summarization-and-compaction/index.md) was built and deliberately left unwired pending budget pressure. There is none. Running a lossy transform to relieve a budget nothing is exceeding is cost without benefit — it turns on when the cap does.

### Choosing a cap you can defend

The sweep is the method. Pick the metric that matters — here, whether the exam still answers correctly from the retrievable tier — and find where it breaks. Then set the cap with margin above that, and **make the metric a test**, so a later change that quietly narrows the margin fails loudly.

What you must not do is tune the cap against average quality. The failure at 16 is not a small degradation in an average; it is one specific fact disappearing, and averages hide exactly that.

## Design decisions

**Evict by salience alone, or protect some memories?** By salience here, and it is not sufficient — the sweep proves it. The obvious repair, an unevictable class, is also not sufficient: the lab's stretch protects diet and loses the employer instead. Protection lists defend the cases you anticipated, and the facts a question depends on vary per question. [What must never be dropped](../compaction-safety/index.md) in I8 takes this up as a budget policy rather than a topic list.

**Demote to `working` or straight to `scratch`?** `working`. One step, so a memory that gets recalled again climbs back rather than falling off a cliff, and so demotion is legible as a gradient rather than a verdict.

**Enforce on write or on read?** On write, in the consolidation pass. On read it would be recomputed per query for a result that changes slowly, and every reader would need to agree on the cap.

## Lab

**You'll implement:** `enforce` and `retrievable`, then the cap sweep.

**Run:**
```
uv run python curriculum/intermediate/budgeted-forgetting/lab/lab.py
```

**Expected output:** the sweep above — correct at 20, broken from 16 down — with the store size **unchanged at 37** at every cap, because nothing is deleted. The lab names the memory whose eviction breaks the answer.

**Stretch:** make dietary facts unevictable and re-run at a cap of 10. The diet survives — and the **employer** is evicted in its place, so the exam still fails. Class-based protection defends only the classes you thought of, and the set of facts a question depends on is not knowable in advance.

That result is worth sitting with: it rules out the obvious fix. [What must never be dropped](../compaction-safety/index.md) in I8 has to be a budget *policy* rather than a list of protected topics, and you have just derived the requirement by measurement instead of being told it.

## What this adds to the capstone

`memlab.forget.budget` — `enforce`, `retrievable`, `Eviction`, `DEFAULT_CAP`. Completes the I5 chain: salience → decay → budget, running after consolidation.

**I5 ends here.** The sixth pinned failure has flipped: salience discriminates across 25 values, memories are tiered, and nothing has been removed from the log. The context exam still fails — retrieval does not yet consult tiers at all, which is the first thing I6 fixes.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| A dietary or safety fact disappears | Cap tuned on averages | Sweep the cap against a correctness metric | Protect classes; test the margin |
| Evicted facts are unrecoverable | Eviction implemented as deletion | Check the log after an eviction | Demote; never remove |
| Quality degrades slowly, unattributably | No metric tied to the cap | Ask what the cap should be and find no answer | Make the sweep a test |
| Memories oscillate in and out | Demotion straight to `scratch` | Watch one memory across passes | Demote one step |
| The cap never binds and is never checked | Mechanism built ahead of pressure, then forgotten | Assert the current headroom | Pin retrievable-vs-cap in a test |

## Check yourself

??? question "The cap does not bind at 37 memories. Why build it now?"
    Because the pressure arrives as slow degradation rather than an incident. There is no day the store becomes too big; there is a year over which answers quietly get worse. Building the mechanism while the store is small enough to reason about is the only time you can verify it does the right thing.

??? question "At cap 16 the system forgets Priya does not eat meat. Is that a bug in eviction?"
    Eviction did exactly what it was told: that memory's salience is 0.413, below the top 16. The bug is that salience is the *only* input to a decision with correctness consequences. Some facts should be unevictable at any score, and finding that out by sweep rather than by incident is the point of the lesson.

??? question "Why demote rather than delete, when the memory has genuinely stopped mattering?"
    Because "stopped mattering" is a heuristic and the store holds the only copy. Demotion is reversible — one reinforcement lifts it back — and deletion is not. The asymmetry is the same one supersession rests on: when one direction is recoverable and the other is not, take the recoverable one.

## Connections

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** intermediate · **~40 min**

**You need first:** [Decay and Memory Tiers](../decay-and-tiers/index.md)

**Concepts assumed:** [Decay](../../../concepts/decay-function.md) · [Salience](../../../concepts/salience.md) · [Supersession](../../../concepts/supersession.md)

**This unlocks:** [Scope, Then Rank](../scope-then-rank/index.md)
<!-- graph:end -->
