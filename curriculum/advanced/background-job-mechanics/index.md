---
id: background-job-mechanics
title: "Background Job Mechanics"
level: advanced
stage: evolve
estimated_minutes: 50
concepts_taught: [lost-update, snapshot-isolation]
concepts_required: [sleep-time-compute, consistency-window, deduplication]
lessons_required: [sleep-time-compute]
capstone_piece: memlab.sleep.job
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Background Job Mechanics

> **In one line.** The job that exists to keep the store correct deletes the correction — all four memories of the job change, and 33 across the run.

## Where this sits

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** advanced · **~50 min**

**You need first:** [Sleep-Time Compute](../sleep-time-compute/index.md)

**Concepts assumed:** [Sleep-Time Compute](../../../concepts/sleep-time-compute.md) · [Consistency Window](../../../concepts/consistency-window.md) · [Deduplication](../../../concepts/deduplication.md)
<!-- graph:end -->

## The problem

Consolidation has been one line since I3:

```python
store.replace(pipeline.consolidate(store.all()))
```

A read, a computation, and a write, with nothing between them. It is correct exactly once — when the corpus has already finished arriving, which is the only situation `ingest()` has ever been in.

Give it a live conversation. A turn lands while the job is computing, and the write-back rewrites the log wholesale:

```
store before the job          31
a turn lands mid-job          32
after the job writes back     31
```

Summed over every position a one-turn job could occupy: **33 memories destroyed**. The worst single turn is session 8 — and it takes the whole announcement:

```
Priya is leaving Northwind Labs
Priya is starting at Calico Systems in January as a staff engineer
Priya works at Calico Systems
Priya is a staff engineer
```

**The batch job that exists to keep the store correct deletes the correction.** And `sleep-time-compute` made this worse: it runs consolidation eleven times instead of once.

## Why this isn't RAG

An indexing job is a pure function of a corpus into a derived structure. Two writers cannot lose each other's work because there is only ever one writer of the index, and if a document arrives mid-run it is simply picked up next time — the corpus is the truth and the index is a cache.

Consolidation writes back into the same store it read. The output is not a cache of the input, it *replaces* it: merged duplicates are gone, losers are retired, confidences are moved. There is no authoritative copy to re-derive from, so a write lost here is lost permanently.

## Mechanism

**Not a lock — a snapshot with a receipt.** The job records *which ids* it read, and the write-back is allowed an opinion about exactly those:

```python
snapshot = read(store)                          # remembers the id set
computed = consolidate(snapshot.memories)
write_back(store, snapshot, computed)
```

Three cases, and the id set is what distinguishes them:

| id | in snapshot | in output | outcome |
|---|---|---|---|
| the job rewrote it | yes | yes | take the job's version |
| the job merged it away | yes | **no** | drop it — deliberate |
| it arrived after the read | **no** | no | **keep it** — not the job's business |

Rows 2 and 3 are indistinguishable in the output: both are simply absent. **Without the recorded id set there is no way to tell "the job deleted this" from "the job never saw it"**, which is precisely why `replace` destroys data — it treats every absence as a deletion.

**The merge is not merely non-destructive; it is correct.** Racing a job against every fourth turn and merging gives a store byte-identical to the serialised run — same 37 memories, same 30 live, same ids:

```
memories destroyed, replace (as shipped)     33
memories destroyed, merge against snapshot    0
```

**And the job is replayable.** Running it twice reports `kept=37, retired=0, untouched=0` and changes nothing, so a crashed job can simply be run again. Idempotence here is not an extra mechanism — it falls out of consolidation already being idempotent (I3) plus a write-back that only claims what it read.

## Design decisions

**Why not a lock?** Because the job takes as long as a full pass over the store, and locking for that duration means the conversation blocks on consolidation — which is the cost `sleep-time-compute` moved off the turn in the first place. A snapshot lets both proceed and reconciles at the end.

**Why not compare-and-set on a store version?** It works, and it fails the whole job when any turn lands — on this corpus that is most of them. Retrying is not free either: the job is the expensive thing. Merging succeeds where a version check would spin.

**Why does the write-back return a report?** Because `kept`, `retired` and `untouched` are the three numbers that distinguish a working job from one quietly discarding writes, and `replace` reports none of them. A job that loses data silently is the failure mode; making it loud is most of the fix.

**What about two jobs at once?** Out of scope here and not out of scope in production. The merge is order-dependent between concurrent jobs touching the same ids — last writer wins on the overlap. One consolidator per user is the assumption, and `memory-observability` is where it gets asserted rather than assumed.

## Lab

**You'll implement:** `read`, `merge`, and `write_back`.

**Run:**
```
uv run python curriculum/advanced/background-job-mechanics/lab/lab.py
```

**Expected output:** the lost update reproduced — **31 → 32 → 31** — then **33** memories destroyed by `replace` against **0** by the merge, the four session-8 memories named, and the raced run proved identical to the serialised one.

**Stretch:** drop `snapshot.ids` and infer "the job saw it" from the computed output instead. Everything passes except the race: a memory that arrived late looks exactly like one the job merged away, and you have rebuilt `replace` with extra steps. **The id set is the entire mechanism.**

## What this adds to the capstone

`memlab.sleep.job` — `Snapshot`, `WriteBack`, `read`, `merge`, `write_back`, `run`. `ingest()` routes through `job.run` whenever `pipeline.sleep` is set, so the shipped path and the one these lessons measure are the same path. It moves no figure: a batch ingest cannot race anything, because the corpus has finished arriving.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Writes vanish during a batch | `replace` treats absence as deletion | Add a memory mid-job; count it after | Merge against a snapshot |
| Deletions stop working | Absence inferred instead of recorded | Merge a duplicate; check it stays gone | Record the id set |
| More consolidation, more loss | Race window multiplied by frequency | Run the gate from A2.1 and re-measure | Guard before scheduling |
| A crashed job cannot be re-run | Write-back not idempotent | Run it twice; diff the store | Idempotent consolidate + scoped write |
| Loss discovered weeks later | Write-back reports nothing | Look for a count of untouched records | Return a report |

## Check yourself

??? question "The job read 31 memories and wrote 31 back. What went wrong?"
    A 32nd arrived in between, and `replace` rewrote the log with a list that could not contain it. Nothing errored and no count looked wrong — the store had exactly the number of memories the job expected. The write is only detectably wrong if you know what the store held at the moment of the write, which is what the snapshot's id set records.

??? question "Why can't the write-back just keep everything in `computed` and add anything missing?"
    Because consolidation removes memories on purpose. A merged duplicate is absent from the output because it was deduplicated, and re-adding it undoes I3 on every run. "Absent from the output" means two opposite things, and only the recorded id set separates them.

??? question "A2.1 gated consolidation to eleven turns. Does that reduce this risk?"
    It increases it. One consolidation had one race window; eleven have eleven, each landing on a turn that just wrote something contested — the memories most worth not losing. The scheduling lesson and this one have to ship together, and this one has to be the guard the other runs behind.

## Connections

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** advanced · **~50 min**

**You need first:** [Sleep-Time Compute](../sleep-time-compute/index.md)

**Concepts assumed:** [Sleep-Time Compute](../../../concepts/sleep-time-compute.md) · [Consistency Window](../../../concepts/consistency-window.md) · [Deduplication](../../../concepts/deduplication.md)
<!-- graph:end -->
