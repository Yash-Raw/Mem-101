---
id: memory-topologies
title: "Memory Topologies"
level: advanced
stage: store
estimated_minutes: 45
concepts_taught: [memory-topology]
concepts_required: [retrieval-scoping, provenance]
lessons_required: [promotion-as-release]
capstone_piece: memlab.agents.topology
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Memory Topologies

> **In one line.** The shape nobody chose gives a low-trust travel agent the user's home address, and the only shape that doesn't leaves it able to see one memory.

## Where this sits

<!-- graph:begin -->
**Stage:** `store` · **Level:** advanced · **~45 min**

**You need first:** [Promotion as a Release](../promotion-as-release/index.md)

**Concepts assumed:** [Retrieval Scoping](../../../concepts/retrieval-scoping.md) · [Provenance](../../../concepts/provenance.md)

**This unlocks:** [Provenance and Trust](../provenance-and-trust/index.md)
<!-- graph:end -->

## The problem

Ask `scopes.partition` what shape this store is and it answers without being asked to have an opinion:

```
priya/*/*                    34
priya/calendar-agent/*        2
priya/travel-agent/*          1
```

Three namespaces: the user's own, and one per writing agent. That is **hierarchical**, and nobody decided it — it fell out of `_agent_memories` filing agent rows under `Scope(user=..., agent=...)` while everything else lands under the bare user scope.

Which is fine, except that a topology is a claim about who can see what, and this one has never been tested against that question.

## Why this isn't RAG

A retrieval corpus has one reader model: whoever can see the index can see the corpus. Multi-tenancy is a deployment concern — separate indexes, separate customers — and within a tenant there is nothing to partition, because a document does not belong to one participant in a conversation.

A memory store has several writers with different trust, writing about the *same person*, into a store that person also reads. The partition is not between customers; it is between an agent and the user it works for, and between agents that do not need each other's material. **The boundary runs inside a single tenant**, which is a shape RAG's read model has no place for.

## Mechanism

**Read the topology off the data, not the design document.** `shape()` reports what the namespaces actually are; the four names are for reasoning, and the store already is one of them.

**Then price each shape by what a reader loses:**

| reader | private | hierarchical | shared |
|---|--:|--:|--:|
| the user | 34 | **37** | 37 |
| calendar-agent | 2 | 36 | 37 |
| travel-agent | 1 | 35 | 37 |

Two things fall out, and neither is the one the diagram suggests.

**For the user, hierarchical and shared are identical.** 37 either way. Whatever isolation the current shape provides, none of it is between the user and their agents — the user reads everything under either.

**For an agent, private is unusable.** The travel agent sees **one** memory: the one it wrote. An agent that cannot read the user it works for is not isolated, it is disconnected.

### And the shape that was chosen for us already leaks

```
travel-agent under private        sees   1 memories, 0 carrying PII
travel-agent under hierarchical   sees  35 memories, 2 carrying PII
travel-agent under shared         sees  37 memories, 2 carrying PII
```

The two are *"Priya lives at 47 Halloway Road, Bristol"* and *"Priya's phone number is 07700 900412"*. **Hierarchical and shared expose exactly the same PII**, to the agent `gold.yml` marks as low-trust and whose one contribution was an unconfirmed rumour about a relocation.

So the trade is not "hierarchical is the safe middle". It is: **hierarchical is a boundary between agents and no boundary at all between the user and an agent.** It costs the travel agent the calendar agent's two rows, and protects nothing the user would care about.

The mechanism that separates them is not a topology, and it is not a read-time filter either — it is a policy about what a given writer is allowed to *see* and *say*, which is `memory-access-control` at the end of this module.

## Design decisions

**Why does `readable` collapse hierarchical and blackboard?** Because they differ on the write side, not the read side. A blackboard is a shared space anyone may write; hierarchical has a common namespace only the user's own path writes to. The read rule is identical, so a function that only reads cannot distinguish them, and pretending otherwise would put a difference in the API that is not in the behaviour.

**Why not just adopt `private` and be done?** Because the number is 1. An agent that can see only its own writes cannot resolve *"remind me what I said about the Spark job"*, cannot avoid re-asking what the user already told someone, and produces exactly the fragmentation Beginner spent a lesson on. Isolation that removes the shared subject removes the point.

**Why measure PII specifically?** Because it is the only category where the cost of a read is not proportional to its usefulness. Thirty-five memories reaching the travel agent is mostly harmless and occasionally load-bearing; two of them are the ones that matter, and no count of *memories* surfaces that. `gold.yml` marks them, and A6 is where they get a mechanism.

## Lab

**You'll implement:** `shape` and `readable`.

**Run:**
```
uv run python curriculum/advanced/memory-topologies/lab/lab.py
```

**Expected output:** the three namespaces (**34 / 2 / 1**) read as **hierarchical**, the reader table above, and the PII counts — **0 under private, 2 under hierarchical, 2 under shared**.

**Stretch:** compute what the *user* loses under private. It is 3 — the agent-written memories — and two of them are the calendar facts that make the assistant useful about Fridays. **Every topology question on this corpus has a small number on one side and a categorical one on the other, and only one of the two is visible in a count.**

## What this adds to the capstone

`memlab.agents.topology` — `Topology`, `Shape`, `shape`, `readable`. Reads through `store.scopes.partition` and `Namespace` rather than reimplementing them; no pipeline stage, because choosing a topology is a deployment decision and this module's job is to price it.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| A topology nobody chose | Namespaces fall out of the write path | Run `shape()` on the live store | Choose it, then assert it |
| Low-trust agent reads PII | Hierarchical treated as a privacy boundary | Count PII visible per reader | A policy, not a topology |
| Agents isolated into uselessness | `private` adopted for safety | Count what each agent can read | Isolate agents, not the subject |
| Read-side fix for a write-side problem | Confusing visibility with authorisation | Ask who may *write* the namespace | See `memory-access-control` |
| Blackboard and hierarchical conflated | They differ only on writes | Ask who may write the common space | Distinguish on the write path |

## Check yourself

??? question "The user sees 37 memories under both hierarchical and shared. What is hierarchical buying?"
    Separation between agents, and nothing else. The travel agent loses the calendar agent's two rows and vice versa. That is worth having — an agent should not accumulate context from tools it does not use — but it is not a privacy property, and reading the diagram as though it were is how the address ends up somewhere it should not be.

??? question "Why is `private` the wrong answer despite leaking nothing?"
    Because the travel agent can then see one memory: its own. Every question that made a shared memory layer worth building — continuity, not re-asking, resolving a reference the user made three sessions ago — needs the agent to read the subject it is working on. Isolation that removes the shared subject is just several small stores.

??? question "The store is already hierarchical. So what changes?"
    That it is now a decision with a measurement attached rather than a side effect of where `_agent_memories` writes. The shape stays; what arrives is knowing it protects the wrong boundary, which is what makes the next three lessons necessary rather than optional.

## Connections

<!-- graph:begin -->
**Stage:** `store` · **Level:** advanced · **~45 min**

**You need first:** [Promotion as a Release](../promotion-as-release/index.md)

**Concepts assumed:** [Retrieval Scoping](../../../concepts/retrieval-scoping.md) · [Provenance](../../../concepts/provenance.md)

**This unlocks:** [Provenance and Trust](../provenance-and-trust/index.md)
<!-- graph:end -->
