---
id: temporal-knowledge-graphs
title: "Temporal Knowledge Graphs"
level: advanced
stage: store
estimated_minutes: 50
concepts_taught: [derivation-graph, cascade-invalidation]
concepts_required: [bi-temporal-modeling, validity-interval, graph-traversal]
lessons_required: [relative-time-resolution]
capstone_piece: memlab.temporal.cascade
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Temporal Knowledge Graphs

> **In one line.** Zero orphans is what you see when the cascade is correct, when its definition is wrong, and when its edges point nowhere — three states, one output.

## Where this sits

<!-- graph:begin -->
**Stage:** `store` · **Level:** advanced · **~50 min**

**You need first:** [Resolving 'Last Week'](../relative-time-resolution/index.md)

**Concepts assumed:** [Bi-Temporal Modeling](../../../concepts/bi-temporal-modeling.md) · [Validity Interval](../../../concepts/validity-interval.md) · [Graph Traversal](../../../concepts/graph-traversal.md)

**This unlocks:** [Sleep-Time Compute](../sleep-time-compute/index.md)
<!-- graph:end -->

## The problem

Carrying validity on graph edges assumes edges. `graph-stores` measured this corpus and found **one node and none**, and A1's parser did not change that:

```
entity graph      {'nodes': 1, 'entity_edges': 0, 'max_hops': 1}
```

But a second graph runs through the store and nobody built it deliberately. Every memory that was summarised, merged or corroborated carries `derived_from`, and **that** is where validity has to travel — because retiring a belief sets `invalid_at` on one record and touches nothing built on top of it.

```
derivation graph  {'derived': 1, 'edges': 1, 'unresolvable': 0}
```

One edge. Small enough to check by hand, which is the only reason the next three findings are visible at all.

## Why this isn't RAG

Re-indexing a corpus is idempotent and total: delete a document, rebuild, and nothing derived from it survives, because nothing derived from it existed. The index is a pure function of the corpus.

A memory store is not. Summaries, merged beliefs and confidence boosts are *written back*, so the store contains conclusions whose evidence is elsewhere in the same store. Retiring the evidence leaves the conclusion standing, at full confidence, with a provenance chain that leads to a retired record. **There is no rebuild to fall back on** — the derivation happened once, against a state that no longer exists.

## Mechanism

**Report unresolvable edges rather than dropping them.** `derived_from` was being written in two namespaces: `summarize` stored memory ids, `promote` stored `provenance.source_id`. A reference into the wrong namespace matches nothing, so a cascade walking these edges finds no orphans — and reports success.

```
derived_from written as source_id:   {'edges': 1, 'unresolvable': 1}   orphans: 0
derived_from written as memory id:   {'edges': 1, 'unresolvable': 0}   orphans: 0
```

Same answer. One of them is a bug. A traversal that silently skips what it cannot resolve cannot tell you which.

**A healthy derived fact is always built on a retired source.** This is the one that gets you. Consolidation retires the loser of a merge and hands its evidence to the winner, so *"every source retired"* describes the normal case, not a broken one:

```
Sam still works nights            live, derived from
  She works nights most of...     retired -- superseded_by: Sam still works nights
```

The naive orphan test flags it, and the naive cascade **retires a correct belief**. The qualifier that fixes it is four words long — retired *by someone other than the derived memory itself* — and with it:

| | orphans | live after cascade |
|---|--:|--:|
| naive definition | **1** | 30 → **29** |
| corrected | **0** | 30 → 30 |

**Cascade runs to a fixed point.** Retiring a derived fact can orphan something derived from *it*. One pass suffices here and would not on a store with summaries of summaries, which is the only reason the loop exists.

### Three states, one output

`orphans == 0` is the reading when the cascade is correct, when its edges point into the wrong namespace, and — had the definition been right and the edges broken — when both. The number that distinguishes them is `unresolvable`, which is why `edges()` reports what it could not resolve instead of returning a shorter list.

## Design decisions

**Why not build the temporal knowledge graph anyway?** Because there is nothing to put on it. Validity on an edge needs edges, and one node has none; the honest deliverable is the measurement plus the machinery that does apply. `graph-stores` made the same call for the same reason, and the two lessons agree because the corpus has not changed.

**Why is `orphans` a report rather than an action?** Because an orphaned conclusion is not automatically wrong — a belief can outlive the evidence that produced it, and re-derivation is a legitimate outcome. What is never acceptable is not knowing. The cascade is the aggressive policy; the list is the one you look at first.

**Why fix the namespace here rather than in `memory-operations`?** Because that is where it was found. It was invisible for two modules and cost nothing until something tried to walk the edge, which is the general property of a broken reference: it has no symptom until a traversal depends on it. `@I1`–`@I8` are unmoved by the fix — the field is in neither the id hash nor any ranking.

## Lab

**You'll implement:** `edges`, `orphans`, and `cascade`.

**Run:**
```
uv run python curriculum/advanced/temporal-knowledge-graphs/lab/lab.py
```

**Expected output:** both graphs measured — **1 node, 0 entity edges**; **1 derived, 1 edge, 0 unresolvable** — then the naive orphan count of **1** against the corrected **0**, and the same **0** produced by a broken namespace for the opposite reason.

**Stretch:** write the naive `orphans` (drop the `superseded_by` qualifier) and run the cascade. It retires *"Sam still works nights"* and every test in this lab still passes except one. **The cascade you cannot audit is the one that quietly deletes correct beliefs.**

## What this adds to the capstone

`memlab.temporal.cascade` — `Edge`, `edges`, `shape`, `orphans`, `cascade`. `evolve/promote.py` now writes memory ids into `derived_from`, matching `summarize`. **Module A1 ends here**: the record has four instants, the parser fills them, three temporal questions route, and derived facts have a graph that can be walked. What it does not yet have is a deletion that uses any of it — that is A6.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Cascade reports nothing, forever | Edges written in two namespaces | Count unresolvable edges | Report, do not drop |
| Cascade retires correct beliefs | Merge losers counted as orphans | Check `superseded_by` on the source | Exclude self-supersession |
| Conclusions outlive their evidence | Retirement touches one record | Walk `derived_from` after a supersession | Cascade or list |
| Validity on edges buys nothing | No edges in the corpus | Measure the graph before adopting it | Measure first |
| Nested summaries survive a cascade | Single-pass propagation | Summarise a summary, retire the root | Run to a fixed point |

## Check yourself

??? question "Both the broken and the fixed version report zero orphans. What makes them distinguishable?"
    `unresolvable`. The traversal has to report the edges it could not follow, because "no orphans found" and "no edges walked" produce identical output otherwise. This is the same argument as `two-clocks` made about the denominator: a number is only meaningful next to the population it was measured over.

??? question "Why does a correct derived fact always look like an orphan?"
    Because merging is how derivation happens here. The winner absorbs the loser, the loser is retired, and the winner's `derived_from` points at it — so "every source retired" is the signature of a healthy merge, not a broken chain. The distinguishing fact is *who* retired it: `superseded_by` pointing back at the derived memory means the retirement was the derivation.

??? question "The entity graph has no edges. Was building the traversal wasted?"
    The traversal that was built is not the entity one. Measuring the entity graph is what showed there was nothing to carry validity on, and that measurement is what redirected the work to `derived_from` — a graph that does exist, that already had a broken edge in it, and that A6's deletion cascade depends on completely.

## Connections

<!-- graph:begin -->
**Stage:** `store` · **Level:** advanced · **~50 min**

**You need first:** [Resolving 'Last Week'](../relative-time-resolution/index.md)

**Concepts assumed:** [Bi-Temporal Modeling](../../../concepts/bi-temporal-modeling.md) · [Validity Interval](../../../concepts/validity-interval.md) · [Graph Traversal](../../../concepts/graph-traversal.md)

**This unlocks:** [Sleep-Time Compute](../sleep-time-compute/index.md)
<!-- graph:end -->
