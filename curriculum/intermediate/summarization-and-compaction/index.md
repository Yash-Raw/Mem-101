---
id: summarization-and-compaction
title: "Summarization and Compaction"
level: intermediate
stage: evolve
estimated_minutes: 45
concepts_taught: [summarization, derived-memory]
concepts_required: [deduplication, token-budget, provenance]
lessons_required: [deduplication]
capstone_piece: memlab.evolve.summarize
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Summarization and Compaction

> **In one line.** Compression comes entirely from what you decline to carry forward — and a summary without `derived_from` is an orphan claim that cannot be rebuilt, traced, or deleted.

## Where this sits

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** intermediate · **~45 min**

**You need first:** [Deduplication](../deduplication/index.md)

**Concepts assumed:** [Deduplication](../../../concepts/deduplication.md) · [Token Budget](../../../concepts/token-budget.md) · [Provenance](../../../concepts/provenance.md)

**This unlocks:** [Semantic Drift](../semantic-drift/index.md)
<!-- graph:end -->

## The problem

Priya's store is 37 memories after deduplication. In two years it will be thousands, and the token budget will still be a few hundred. Something has to compress.

The obvious move is a summary per session. Build one, measure it, and the first result is not what you expect:

| session | sources kept | compression |
|---|--:|--:|
| s1 | 4 | 0.95 |
| **s2** | 2 | **1.22** |
| **s4** | 2 | **1.40** |
| s5 | 3 | 0.84 |

Two sessions got **bigger**. The summary of session 4 is 1.4× the size of session 4.

Nothing is broken. An extractive summary that keeps every claim is not a compression — it is a re-joining, and it pays for the joining. Sessions 2 and 4 contain nothing but semantic claims, so there was nothing to drop, and the summary added punctuation to a list it kept whole.

**Compression is entirely a function of what you throw away.** That reframes the design question from *how do I summarise* to *what am I willing to lose*, which is a question with a defensible answer.

## Why this isn't RAG

Document summarisation produces a new artifact beside a corpus that stays put. The original is still there, unchanged, and the summary is a convenience — delete it and rebuild it any time.

A memory summary is meant to **replace** what it summarises, or it saves nothing. That makes it load-bearing: something must record what it was built from, so it can be rebuilt when a source changes and deleted when a source is deleted. Otherwise you get the failure `deletion-that-actually-deletes` is named for — you removed the episode, and the summary still knows.

## Mechanism

**What gets dropped: episodes.** Sessions are summarised from their semantic and procedural claims only. That is a real, arguable choice — episodes are the record of *what happened*, and a summary of them loses the timestamps that made them worth keeping. Standing beliefs compress; dated events should be archived or forgotten, not blurred.

Across the store that yields **1461 → 1175 characters**, about 0.80. Modest, and honest: the compression is exactly the size of what was dropped.

**What makes it safe: `derived_from`.**

```python
summary = Memory(
    content=f"Summary of {session}: {claims}",
    derived_from=tuple(sorted(m.id for m in members)),   # every source, by id
)
```

This is a field the Beginner record did not have, added here because summarisation is the first thing that needed it. Worth pausing on the cost of that timing: adding a defaulted field now is a one-line change, and adding it after a million summaries exist means backfilling provenance that was never recorded — which is impossible, not merely expensive. `the-memory-record` argued the schema is the one irreversible decision; this is what "irreversible" costs when you get it slightly wrong, and it is cheap here only because the store is small.

`orphaned_summaries` is the check that makes the field earn its place: after any deletion, a summary whose sources are no longer all live is stale at best and a privacy violation at worst.

**Extractive, not generative.** Every sentence in the summary exists verbatim in the store, so every claim is attributable and none can be invented. Generative summaries read better and lose that: a fluent sentence covering three memories cannot be traced to any of them, and a hallucinated one cannot be distinguished from a real one. Fluency is worth less than provenance here.

## Design decisions

**Summarise per session, or rolling across sessions?** Per session, because the session is a natural boundary the corpus already carries and it keeps `derived_from` small and stable. Rolling windows re-derive far more on every change.

**Keep the sources after summarising?** Yes, at this scale — a summary that replaces its sources is only safe once you are certain nothing else needs them, and archival is a Level 3 decision under real cost pressure. `derived_from` is what makes deferring that decision possible.

**Drop episodes, or drop by salience?** Episodes, deliberately, because it is a rule you can state and defend. Salience-based dropping is better and needs a salience signal that does not exist until I5 — and a lossy rule you cannot explain is worse than a blunt one you can.

## Lab

**You'll implement:** `summarise_session` with `derived_from`, and `orphaned_summaries`.

**Run:**
```
uv run python curriculum/intermediate/summarization-and-compaction/lab/lab.py
```

**Expected output:** 10 session summaries; the per-session compression table above, including the two that expand; the whole-store figure of **0.80**; then a source is deleted and `orphaned_summaries` detects exactly one stale summary.

**Stretch:** compute compression against the summary's own sources rather than the whole session. Every number goes above 1.0 and the technique looks useless — the correct answer to the wrong question. Choosing the denominator *is* the measurement.

## What this adds to the capstone

`memlab.evolve.summarize` — `summarise_session`, `summarise_all`, `orphaned_summaries`, `Summary`. And `Memory.derived_from`, which [semantic drift](../semantic-drift/index.md) needs immediately and cascade deletion needs in Advanced.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Summaries make the store bigger | Nothing was dropped | Measure compression per session; look for >1.0 | Decide explicitly what to lose |
| Deleted data survives in a summary | No `derived_from` | Delete a source, grep summaries for its content | Record sources; run `orphaned_summaries` |
| A summary claims something no source said | Generative summarisation | Check each claim appears verbatim in a source | Extractive, or verify claims |
| Summaries go stale silently | Sources changed, summary not rebuilt | Compare summary age to newest source | Re-derive on source change |
| Dates vanish from history | Episodes summarised away | Ask when something happened | Summarise beliefs; archive episodes |

## Check yourself

??? question "Session 4's summary is 1.4× the size of session 4. Is the summariser broken?"
    No — session 4 contains two semantic claims and no episodes, so there was nothing to drop and the summary re-joined them with punctuation. It is a correct summary of a session that had no redundancy. The lesson is that compression is not a property of the summariser, it is a property of what the input allows you to discard.

??? question "Why record `derived_from` when the summary text already contains the claims verbatim?"
    Because text matching is not identity. Two memories can share wording, a source can be edited, and a claim can appear in several sessions. Deletion and rebuild both need to know *which records* this was built from, and only ids answer that.

??? question "`derived_from` was added in Level 2, after the record was supposedly settled. Doesn't that undercut the earlier lesson?"
    It illustrates it. Adding a defaulted field is trivial *now*, with 37 memories and no summaries in existence. The same change after a million summaries means backfilling links that were never recorded — and that data does not exist to be recovered. The schema is not unchangeable; it is unchangeable *cheaply*, and the window closes quietly.

## Connections

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** intermediate · **~45 min**

**You need first:** [Deduplication](../deduplication/index.md)

**Concepts assumed:** [Deduplication](../../../concepts/deduplication.md) · [Token Budget](../../../concepts/token-budget.md) · [Provenance](../../../concepts/provenance.md)

**This unlocks:** [Semantic Drift](../semantic-drift/index.md)
<!-- graph:end -->
