---
id: implicit-signals
title: "Behaviour as Memory"
level: advanced
stage: extract
estimated_minutes: 50
concepts_taught: [implicit-signal, correction-as-label]
concepts_required: [user-model, consistency-window, provenance]
lessons_required: [from-facts-to-a-user-model]
capstone_piece: memlab.user.signals
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Behaviour as Memory

> **In one line.** The cheapest correction signal in the system is the user saying *"remember?"* — and acting on it costs nothing, fixes eight of eleven wrong turns, and cannot touch the three that matter most.

## Where this sits

<!-- graph:begin -->
**Stage:** `extract` · **Level:** advanced · **~50 min**

**You need first:** [From Facts to a User Model](../from-facts-to-a-user-model/index.md)

**Concepts assumed:** [User Model](../../../concepts/user-model.md) · [Consistency Window](../../../concepts/consistency-window.md) · [Provenance](../../../concepts/provenance.md)

**This unlocks:** [Personalization Without Creepiness](../applying-the-model/index.md)
<!-- graph:end -->

## The problem

Every memory in this store came from something the user **asserted**. The transcript also contains them *reacting* to what the assistant said, and none of that is collected:

```
memories recording any use at all:  0 of 37
```

`access_count` is zero everywhere. Nothing knows a belief has ever been retrieved, let alone retrieved and rejected.

And there is a rejection, in session 9:

```
assistant   How are you finding it compared to your work at Northwind Labs?
user        I left Northwind last month, remember? I'm at Calico now.
```

A negative example with a target attached — the assistant named the belief in its own words, so the belief is identifiable without a retrieval log.

## Why this isn't RAG

A retrieval system has implicit signals too, and they are about *documents*: clicks, dwell time, thumbs. They tune ranking — which document to show — and the corpus is unaffected either way.

Here the signal is about a **belief**, and the correct response is not to rank it lower but to stop believing it. The user is not expressing a preference between sources; they are telling you a fact about the world changed and you missed it. That is a write-path event that arrived through the read path, and nothing in the architecture is listening.

## Mechanism

**Pair the turns.** A correction is a user turn that rejects the assistant's *immediately preceding* turn. Without the pairing it is not a signal — a user changing their mind unprompted is an ordinary write, not evidence that a belief was wrong.

**Match narrowly.** A broad pattern turns every *"no"* into a correction, including *"still no meat"*, which is a dietary fact. A false correction retires a belief that was right, so precision beats recall here by a wide margin. Four patterns find one correction in twenty-four turns.

**Attribute from the assistant's own words.** The assistant said *"your work at Northwind Labs"*, and content overlap points at `Priya is a data engineer at Northwind Labs` — the right memory. A retrieval log would be better, and this course does not keep one; that absence is itself a finding, and `memory-observability` is where it lands.

### What it buys

Replaying the corpus turn by turn, against a store consolidated after every turn:

| policy | runs | embed | cosine | wrong turns | live |
|---|--:|--:|--:|--:|--:|
| defer everything | 1 | 38 | 282 | **11** | 30 |
| consolidate on a contested slot | 11 | 281 | 1011 | **0** | 30 |
| **act on corrections, never consolidate** | **1** | **38** | **260** | **3** | 30 |

**Eleven wrong turns become three, at the cost of the row that does nothing.** Same single consolidation, same 38 embeddings — and *fewer* comparisons, because retiring the belief early leaves less to compare.

`sleep-time-compute` bought the same correctness with eleven consolidation passes and 281 embeddings. This buys most of it with none, because **the user did the work**: they named the wrong belief out loud.

**Why three remain, and why they are the worst three.** The eager store retires Northwind at turn 14 — session 8, where she announces the move. The correction arrives at turn **17**. Turns 14, 15 and 16 are the window in which *the user has already told you* and the store has not caught up, and no signal from the user can close it, because there is nothing to react to until the assistant gets it wrong out loud.

Filter the signal by *session* rather than by turn and you get two instead of three — the correction fires from the first turn of session 9, one turn before she utters it. A signal applied before it is given is not a measurement of the signal.

## Design decisions

**Why not replace the A2.1 gate with this?** Because three is not zero, and the three turns it cannot fix are the ones where the user has already told you the new fact and the store has not caught up. A signal that only fires when the user is annoyed is a fallback, not a policy. They compose: consolidate on contested slots, and treat a correction as an immediate, targeted retirement.

**Why retire rather than lower confidence?** Because the user did not express doubt. *"I left Northwind last month, remember?"* is a first-party assertion that the belief is false, which is exactly what supersession is for — and the audit trail is preserved either way, so nothing is lost by acting decisively.

**Why not learn a correction model?** Because the failure mode of a probabilistic detector here is retiring a true belief on a false positive, and there is no signal that would tell you it happened. Four regexes that find one correction and no false ones are worth more than a classifier that finds three and invents one.

**Repetition and abandonment are not implemented.** The corpus has no unambiguous instance of either — the diet is restated three times, but each restatement *refines* rather than repeats, which I3 established is a different relation. Building detectors for signals the corpus does not contain means the first real instance meets untested code.

## Lab

**You'll implement:** `corrections` and `attribute`.

**Run:**
```
uv run python curriculum/advanced/implicit-signals/lab/lab.py
```

**Expected output:** **0 of 37** memories recording any use, the single correction found in session 9 attributed to the Northwind belief, and the three-row table — **11**, **0**, **3** wrong turns.

**Stretch:** widen the correction pattern to any turn containing *"no"* or *"not"*. It fires on *"Still no meat, but pescatarian now"* and retires `Priya does not eat meat` — a belief that is true, that the user had just restated, and that the exam depends on. **The cost of a false correction is a true belief, deleted, with the user's own words cited as the reason.**

## What this adds to the capstone

`memlab.user.signals` — `Correction`, `corrections`, `attribute`, `used`. No pipeline stage: acting on a correction is a write triggered by a read, and the seam for that is `retrieve.triggers`, which `retrieving-procedures` reaches at the end of A5.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| True beliefs quietly retired | Correction pattern too broad | Check what each match targets | Narrow patterns; pair the turns |
| Corrections invisible | Only assertions extracted | Count memories with `access_count` | Read the reaction, not just the claim |
| Signal fires on a fresh statement | No assistant turn paired | Require the preceding turn | Pair before matching |
| Signal appears to work early | Filtered by session, not by turn | Compare the fix turn to the utterance turn | Filter by timestamp |
| Correct belief blamed | Attribution by recency, not content | Check the target against the words used | Match the assistant's own turn |
| Detector for a signal you lack | Built for repetition/abandonment unseen | Count instances in the corpus | Build what you can measure |

## Check yourself

??? question "Acting on corrections costs nothing and fixes eight of eleven turns. Why keep the A2.1 gate?"
    Because the three it cannot fix are the ones where the user *already told you* the new fact and the store had not caught up — turns 14 to 16, between the announcement and the complaint. A policy that only corrects when the user objects has made being wrong the trigger. The gate prevents; the signal recovers, and it can only recover after the damage.

??? question "Why is a false correction worse than a missed one?"
    Because it retires a belief that was true, and the audit trail records the user's own words as the justification. A missed correction leaves a stale fact that the next consolidation catches anyway. This asymmetry is why the pattern is four narrow expressions rather than a general notion of disagreement.

??? question "The attribution works by matching the assistant's words. What would be better, and why isn't it here?"
    A retrieval log — which memories were actually in the context when the assistant spoke. This course does not keep one, so attribution reconstructs from the output instead. It works because the assistant quoted the belief, and it would fail the moment a response paraphrased. That gap is `memory-observability`'s subject.

## Connections

<!-- graph:begin -->
**Stage:** `extract` · **Level:** advanced · **~50 min**

**You need first:** [From Facts to a User Model](../from-facts-to-a-user-model/index.md)

**Concepts assumed:** [User Model](../../../concepts/user-model.md) · [Consistency Window](../../../concepts/consistency-window.md) · [Provenance](../../../concepts/provenance.md)

**This unlocks:** [Personalization Without Creepiness](../applying-the-model/index.md)
<!-- graph:end -->
