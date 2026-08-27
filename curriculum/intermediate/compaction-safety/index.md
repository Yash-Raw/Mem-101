---
id: compaction-safety
title: "What Must Never Be Dropped"
level: intermediate
stage: assemble
estimated_minutes: 40
concepts_taught: []
concepts_required: [eviction, token-reservation, slot]
lessons_required: [ordering-and-formatting]
capstone_piece: memlab.assemble.pinning
lab: lab/lab.py
lab_runtime: fake
status: published
---

# What Must Never Be Dropped

> **In one line.** `budgeted-forgetting` proved a protected-topic list evicts something else instead — so the policy has to be derived from the question, and even then it does not save you.

## Where this sits

<!-- graph:begin -->
**Stage:** `assemble` · **Level:** intermediate · **~40 min**

**You need first:** [Ordering and Formatting](../ordering-and-formatting/index.md)

**Concepts assumed:** [Eviction](../../../concepts/eviction.md) · [Token Reservation](../../../concepts/token-reservation.md) · [Slot](../../../concepts/slot.md)

**This unlocks:** [Does This Earn Its Tokens?](../slot-value/index.md)
<!-- graph:end -->

## The problem

I5 ended on a specific failure. Tightening the eviction cap made the system forget that Priya does not eat meat; protecting dietary facts saved the diet and **evicted the employer instead**. A protected-class list defends only the classes someone thought of, and the facts a question depends on vary per question.

The same problem arrives at assembly. `Priya is a staff engineer` is true, well-scored, and takes the tokens `Priya has a gluten intolerance` needs. Ranking cannot help: it is a *better* answer to the employer question, and ranking orders within a question.

## Why this isn't RAG

A truncated document context loses supporting evidence and the answer degrades gracefully. Nothing in a passage is *safety-critical* by virtue of being a passage.

Memories are not interchangeable that way. A dietary restriction, an allergy, a standing instruction — dropping one is not a slightly worse answer, it is a confidently wrong one about something that matters. The production failure this is named for is a compaction step silently discarding a safety constraint from a system prompt, and the symptom is a model that stops following an instruction nobody realises it can no longer see.

## Mechanism

**Not a topic list.** The policy is derived from the query:

> every slot the question asked about must be covered in context

`slots_for(query)` already exists — `query-formulation` built it, reusing the `SLOTS` table from `contradiction-detection`. Pinning takes the same vocabulary and turns it into a budget guarantee: cover each asked slot breadth-first, then depth, then fill.

```python
for depth in range(per_slot):
    for slot in sorted(by_slot):
        ...
```

Breadth first, so a question with three relevant facts is not starved by a question with one.

### Measured: it does not flip the target

| budget | score order | pinned |
|--:|---|---|
| 80 | PASS | PASS |
| 77 | PASS | PASS |
| 70 | fail | fail |
| 67 | fail | fail |

**Identical.** Breadth-first coverage reaches `staff engineer` at depth 1 of the employer slot before it reaches `gluten` at depth 2 of the diet slot — so the padding still gets there first.

That is the third policy in this module to change nothing, and by now the pattern is the point: **allocation policies cannot solve a problem whose cost is fixed framing.** They are still correct, and they will matter on a corpus where a question's facts are unevenly distributed across slots. Here they are load-bearing for a case this data does not contain.

**What pinning does buy** is a stated invariant. Without it, "the diet question got no facts" is a possible outcome nothing forbids. With it, that outcome fails a check rather than producing a confident answer about food.

## Design decisions

**Derive from the query, or maintain a list?** Derive. I5 measured what a list costs: protecting diet evicted the employer, and the next question would have needed a class nobody added. A query-derived policy adapts per question, which is the only thing that can.

**Cap per slot?** Three, and it is arbitrary — chosen so a slot with several relevant facts can use them without one slot taking the whole context. A budget makes the cap mostly moot; it matters when the budget is generous and the ranking is flat.

**Should pinning be able to exceed the budget?** No. A pinned memory that does not fit is still dropped, and the context is honest about being incomplete. A policy that overruns the budget to satisfy itself produces a context the model cannot receive, which is not safer.

## Lab

**You'll implement:** `required` and `unpinned`, then the comparison.

**Run:**
```
uv run python curriculum/intermediate/compaction-safety/lab/lab.py
```

**Expected output:** the slots the exam asks about, the pinned set breadth-first, and the table above — **pinning identical to score order at every budget**. Then the invariant it does buy: every asked slot covered, asserted rather than hoped for.

**Stretch:** construct a query whose slots are unevenly served — one slot with four relevant facts, another with one — and re-run. Pinning now changes the outcome, because breadth-first is the whole point when depth is uneven. **A policy that is a no-op on your data is not a policy that is wrong.**

## What this adds to the capstone

`memlab.assemble.pinning` — `required`, `unpinned`, wired into `pack(pin=True)` and switched on by the `intermediate` profile.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| A safety constraint silently absent | Compaction dropped it with no check | Assert asked slots are covered | Query-derived pinning |
| Protecting one class loses another | A topic list rather than a policy | Sweep the budget; see what leaves | Derive from the query |
| One slot takes the whole context | Depth-first coverage | Count facts per slot in context | Breadth first, then depth |
| A context the model cannot receive | Pinning allowed to exceed the budget | Check assembled tokens against the budget | Pinned memories still have to fit |
| Confident answers from partial context | No incompleteness signal | Ask whether the context knows what it is missing | Fail the check, do not paper over it |

## Check yourself

??? question "Pinning changes nothing measurable. Why ship it?"
    Because it converts a possible silent failure into a checkable invariant. Without it, *"the diet question got no facts and the model answered anyway"* is an outcome nothing forbids — it simply has not happened yet on this corpus. The lab's stretch constructs the case where it does.

??? question "Three policies in this module, three no-ops. Is context assembly not worth doing?"
    It is worth doing and this module is where you learn *which layer* the cost lives in. Packing, formatting and pinning are all correct and all reorder memories, and the largest single element in this context is not a memory at all. Ruling out three layers is what makes the fourth obvious.

??? question "Why must a pinned memory still fit the budget?"
    Because a context that exceeds the budget is not delivered — it is truncated by something downstream with no idea what mattered, or rejected outright. A safety policy that produces an undeliverable context has made things worse, not safer.

## Connections

<!-- graph:begin -->
**Stage:** `assemble` · **Level:** intermediate · **~40 min**

**You need first:** [Ordering and Formatting](../ordering-and-formatting/index.md)

**Concepts assumed:** [Eviction](../../../concepts/eviction.md) · [Token Reservation](../../../concepts/token-reservation.md) · [Slot](../../../concepts/slot.md)

**This unlocks:** [Does This Earn Its Tokens?](../slot-value/index.md)
<!-- graph:end -->
