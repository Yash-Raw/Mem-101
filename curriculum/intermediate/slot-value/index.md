---
id: slot-value
title: "Does This Earn Its Tokens?"
level: intermediate
stage: assemble
estimated_minutes: 45
concepts_taught: [element-cost, irreducible-context]
concepts_required: [token-reservation, context-assembly]
lessons_required: [compaction-safety]
capstone_piece: memlab.assemble.value
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Does This Earn Its Tokens?

> **In one line.** Three packing policies moved nothing; the largest single element in the context was never a memory — and pricing it takes the answer from 80 tokens to 52.

## Where this sits

<!-- graph:begin -->
**Stage:** `assemble` · **Level:** intermediate · **~45 min**

**You need first:** [What Must Never Be Dropped](../compaction-safety/index.md)

**Concepts assumed:** [Token Reservation](../../../concepts/token-reservation.md) · [Context Assembly](../../../concepts/context-assembly.md)
<!-- graph:end -->

## The problem

`the-packing-problem` ruled out allocation. `ordering-and-formatting` found six tokens. `compaction-safety` bought an invariant and moved no number. Three plausible mechanisms, all correct, none of them touching the target.

Price every element instead of just the memories — shares are of the 77 tokens the audit prices:

| element | tokens | share |
|---|--:|--:|
| **framing header** | **29** | **38%** |
| Priya works at Calico Systems | 11 | 14% |
| Priya does not eat meat | 9 | 12% |
| Priya eats fish | 7 | 9% |
| Priya is a staff engineer | 10 | 13% |
| Priya has a gluten intolerance | 11 | 14% |

**Nearly two fifths of the context is not a memory.** Every policy so far has been optimising the other 62%.

## Why this isn't RAG

A retrieval prompt has framing too, and it is usually a fixed prefix nobody counts because the context is thousands of tokens and the framing is dozens.

A memory context is *small* — five memories, eighty tokens — because the whole design is selecting a few things worth saying. At that scale a fixed prefix is not overhead, it is **two fifths of the payload**, and the arithmetic that makes it invisible in RAG is exactly what makes it dominant here.

## Mechanism

**The header is not waste.** `context-assembly-v0` measured what it buys: under an assertive framing a model defends a stale fact against the user correcting it; under *"recalled beliefs… may be out of date"* it updates. It is the cheapest reliability improvement in the system.

So *"does it help?"* is the wrong question. **Everything in a context helps, or it would not be there.** The question is what it costs and what it displaces — and at a tight budget this header displaces a dietary restriction.

**Right-size it, do not remove it:**

```
Here is what you remember about this user. These are recalled beliefs,
not verified facts, and some may be out of date:          29 tokens

Recalled about this user (may be out of date):            11 tokens
```

*Recalled* carries the belief framing. *May be out of date* carries the staleness warning. The long version says both twice, and 18 tokens is one more fact.

### The result

| budget | before I8 | after |
|--:|---|---|
| 80 | PASS | PASS |
| 67 | fail | **PASS** |
| 60 | fail | **PASS** |
| 55 | fail | **PASS** |
| **52** | fail | **PASS** |
| 50 | fail | fail |

**The exam survives a 52-token context**, down from needing 80. Compact framing and year precision together, and neither packing policy contributed.

### And 52 is not the floor

The four required facts plus a compact header come to **43 tokens**. No policy in this module reaches it.

The nine-token gap is `Priya is a staff engineer` — a genuine second answer to the employer question, scored between the two diet facts, and the packer has no basis to reject it. **Nothing in the system knows that the employer question needs one fact while the diet question needs three.** That is not an optimisation left on the table; it is the point where context assembly runs out of information.

Knowing where that point is matters more than shaving it. A system that reports *"52 with this policy, 43 in principle"* can be reasoned about; one that reports *"we compress well"* cannot.

## Design decisions

**Right-size or remove?** Right-size. Removal saves 11 more tokens and re-introduces the failure Beginner measured — a model arguing with a user about their own life. The reliability was never the thing to trade.

**Is 11 tokens optimal?** Almost certainly not, and it does not matter: below the floor of 43 no header length flips anything, and the boundary is set by the facts. Optimising past the binding constraint is the mistake this lesson is about.

**Should the audit run in production?** Yes — as a share, not a count. A header that is 38% of a five-memory context is 3% of a 900-token one, and the same code is fine in one and wrong in the other. Watch the share.

## Lab

**You'll implement:** `audit` and `floor_for`.

**Run:**
```
uv run python curriculum/intermediate/slot-value/lab/lab.py
```

**Expected output:** the cost table above with the header at **38%**, then the budget sweep flipping at **52**, and the derived floor of **43** with the nine-token gap attributed to a single memory.

**Stretch:** compute the header's share at k=20 instead of k=5. It falls to about a tenth, and the compaction is pointless — the same header, the same code, and an optimisation that has stopped mattering. **Element cost is a ratio, and a ratio needs both terms measured.**

## What this adds to the capstone

`memlab.assemble.value` — `audit`, `ElementCost`, `floor_for`, `COMPACT_HEADER`. The `intermediate` profile switches on `assemble`, combining compact framing, year precision and pinned coverage.

**Milestone 2c ends here, and so does the Intermediate level.** `memlab` v0.2: beliefs correct from I4, reachable from I6, and surviving a 52-token context from I8. Six of the seven failures Beginner catalogued are fixed; the deletion cascade is Advanced's.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Budget work moves nothing | Optimising memories while framing dominates | Price every element, not just the memories | An audit |
| A model argues with a correction | Header removed to save tokens | Correct it mid-conversation | Right-size; never remove |
| Compaction effort with no payoff | Optimising past the binding constraint | Compute the floor; compare to what you reach | Know the floor |
| A fix that stopped mattering | Element cost as a count, not a share | Recompute the share at a different k | Watch the ratio |
| Confident answers from partial context | No floor and no incompleteness signal | Ask what the context is missing | Report the gap |

## Check yourself

??? question "The header costs 38% of the context and improves reliability. Which wins?"
    Neither, as stated — the question is malformed. Everything in a context helps or it would not be there, so *"does it help"* never discriminates. Pricing it does: 29 tokens buys belief framing, 11 tokens buys the same framing, and the difference buys a dietary restriction.

??? question "Why is 43 unreachable when the packer can see all five hits?"
    Because it cannot tell that one of them is redundant. `Priya is a staff engineer` is a real second answer to a real question, scored between the two diet facts. Nothing in the system encodes that the employer question is satisfied by one fact while the diet question needs three, and no ranking or packing policy can infer it.

??? question "Three no-ops and one lever. Was the rest of this module wasted?"
    The three are what make the fourth findable. Each ruled out a layer, and without them the header trim looks like a lucky guess rather than the consequence of pricing everything and seeing where the cost actually sits. Ruling out a plausible mechanism by measurement is a result.

## Connections

<!-- graph:begin -->
**Stage:** `assemble` · **Level:** intermediate · **~45 min**

**You need first:** [What Must Never Be Dropped](../compaction-safety/index.md)

**Concepts assumed:** [Token Reservation](../../../concepts/token-reservation.md) · [Context Assembly](../../../concepts/context-assembly.md)
<!-- graph:end -->
