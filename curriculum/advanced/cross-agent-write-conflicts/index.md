---
id: cross-agent-write-conflicts
title: "Cross-Agent Write Conflicts"
level: advanced
stage: evolve
estimated_minutes: 50
concepts_taught: [cross-writer-conflict]
concepts_required: [competence, memory-operations, provenance]
lessons_required: [provenance-and-trust]
capstone_piece: memlab.agents.conflicts
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Cross-Agent Write Conflicts

> **In one line.** The rule that stops a rumour is a cliff, not a slope — and an agent one notch above it overwrites the user's own belief just by being newer.

## Where this sits

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** advanced · **~50 min**

**You need first:** [Provenance and Trust](../provenance-and-trust/index.md)

**Concepts assumed:** [Competence](../../../concepts/competence.md) · [Memory Operations](../../../concepts/memory-operations.md) · [Provenance](../../../concepts/provenance.md)

**This unlocks:** [Memory Access Control](../memory-access-control/index.md)
<!-- graph:end -->

## The problem

Measure before inventing a problem. Conflict candidates over the **unconsolidated** store:

```
27 candidate pairs
   agent vs user    1     the relocation rumour against the address
   agent vs agent   0
```

One cross-writer conflict in the whole corpus, and I4 already gets it right. The travel agent arrives at authority 0.3, `arbitrate`'s first rule sees a relayed claim against a first-party one, and the address wins regardless of dates.

So the machinery works on the case that exists. The question is what it does one notch away from it.

## Why this isn't RAG

Two documents disagreeing is not a problem a retrieval system has to solve. It returns both, ranked, and the model reconciles them in context — or does not, and the user sees two sources and decides. Nothing is destroyed.

A memory layer must *pick*, because the loser is retired and stops being retrievable. And the pick is made by a policy that is invisible to whoever wrote the losing claim. **A silent, permanent, unattributable decision** is a different object from a ranked list, and it is why `deterministic-freshness` insisted rules do this rather than a model.

## Mechanism

**`FIRST_PARTY` is a threshold at 0.5, and that is the whole finding.** Rule 1 asks whether each writer is above the line, not how far:

```
user says          "pescatarian"   2025-08-02   authority 1.0
calendar agent says "vegetarian"   2026-06-01   authority 0.9

by authority   rule=recency     winner=calendar-agent
by trust       rule=authority   winner=the user
```

Both are above 0.5, so rule 1 does not discriminate, and arbitration falls through to **recency** — where the agent wins for the only reason it could, being newer. An agent trusted for scheduling has overwritten a dietary belief the user stated themselves.

`provenance-and-trust` built the fix without wiring it: score the **claim**. A calendar agent asserting diet is out of domain, so its trust is 0.3, which is below the line, and rule 1 discriminates again. The substitution is one argument — `arbitrate(a, b, claim_trust)` — and it is now what `@A3` runs.

### And it changes nothing here

```
@A3 store contents == @A2 -- same ids, same validity, same supersessions
```

The one real cross-writer pair is a 0.3 relay, and its out-of-domain discount lands exactly on the authority it already had. **The mechanism is correct and this corpus cannot demonstrate it**, which is worth stating rather than staging — the same call `graph-stores` made about a corpus with one node.

What the corpus *does* demonstrate is the shape of the gap: zero agent-versus-agent conflicts, because the two agents claim disjoint slots. `residence` from one, nothing nameable from the other. A store with two calendar integrations, or a personal and a work assistant, would have this problem constantly; this one has it never.

**Run candidate generation on the unconsolidated store.** After reconciliation the losers are retired and excluded from candidate generation, so the same call returns zero — and the absence looks like a fact about the corpus rather than about when you asked. That is how you measure this as "no conflicts" and ship.

## Design decisions

**Why not make `FIRST_PARTY` a gradient?** Because the rule is a *precedence*, not a score: a relayed claim never beats a first-party one, at any date. Turning it into a weighted sum reintroduces exactly the tunable that `deterministic-freshness` removed, and the failure mode is a threshold nobody can explain when a user asks why their own statement lost.

**Why score the claim rather than raise the agent's bar?** Dropping the calendar agent to 0.4 would fix this pair and break the case it exists for — a calendar agent reporting a schedule change *should* win against a stale user statement. The problem is not that the agent is trusted too much; it is that trust was being asked a question it does not answer.

**Why is agent-versus-agent zero and left alone?** Because it is zero. Building arbitration for a case the corpus does not contain means the first real instance meets untested code, and the honest deliverable is the measurement plus a `CrossWriter` that reports `agent_versus_agent` so the day it stops being zero is visible.

## Lab

**You'll implement:** `cross_writer` and `decided_by`.

**Run:**
```
uv run python curriculum/advanced/cross-agent-write-conflicts/lab/lab.py
```

**Expected output:** **1** cross-writer pair, agent-versus-agent **False**, then the two arbitrations — the 0.3 relay decided by **authority** either way, and the 0.9 agent decided by **recency** under authority and by **authority** under trust, with the winner changing.

**Stretch:** raise the travel agent's authority from 0.3 to 0.6 and re-run the corpus. The relocation rumour crosses the line, wins on recency, and the user's address is retired — one constant in a fixture, and the store now believes a colleague's speculation. **Every defence in this module is one number away from not being one.**

## What this adds to the capstone

`memlab.agents.conflicts` — `CrossWriter`, `cross_writer`, `decided_by`, `above_the_line`. `arbitrate`, `decide`, `decide_all` and `reconcile` gain an optional `trust` argument, defaulting to raw authority so every earlier snapshot is unmoved; `Pipeline.trust` switches `claim_trust` on at A3.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Agent overwrites a user's own belief | Threshold rule stops discriminating above the line | Arbitrate a 0.9 agent against a 1.0 user | Score the claim |
| "No conflicts found" | Measured after reconciliation retired them | Run candidate generation pre-consolidation | Measure the right set |
| Fix breaks the case it was for | Agent's authority lowered globally | Test a schedule claim from the calendar agent | Per-claim, not per-writer |
| Untested path on first real instance | Built for a case the corpus lacks | Count agent-vs-agent pairs | Report zero, don't simulate |
| A defence one constant from failing | Authority set in a fixture, never asserted | Raise it and re-run | Assert the threshold gap |

## Check yourself

??? question "Both writers are above `FIRST_PARTY`. Which rule decided, and was it wrong?"
    Recency, and it was working exactly as specified — the newer claim about the same attribute wins. The error is upstream: rule 1 was asked "is this writer first-party?" when the question needed was "is this writer first-party *about this*?". Recency then arbitrated a pair it should never have been handed.

??? question "`@A3` is byte-identical to `@A2`. Why ship the change?"
    Because the corpus contains one cross-writer conflict and it happens to be the case the old rule already handled. The substitution is a no-op here and decisive one notch away, and the alternative — waiting for a corpus that exhibits it — means the first real instance meets code nobody has run. The measurement is the honest part: it says the mechanism is unproven *on this data*, not that it is unnecessary.

??? question "Why measure candidates before consolidation rather than after?"
    Because reconciliation retires the losers, and retired memories are excluded from candidate generation. Ask afterwards and you get zero — a clean number that describes your timing rather than your corpus, and reads exactly like "we have no cross-writer conflicts."

## Connections

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** advanced · **~50 min**

**You need first:** [Provenance and Trust](../provenance-and-trust/index.md)

**Concepts assumed:** [Competence](../../../concepts/competence.md) · [Memory Operations](../../../concepts/memory-operations.md) · [Provenance](../../../concepts/provenance.md)

**This unlocks:** [Memory Access Control](../memory-access-control/index.md)
<!-- graph:end -->
