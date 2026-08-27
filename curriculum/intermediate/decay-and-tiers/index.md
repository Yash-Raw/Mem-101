---
id: decay-and-tiers
title: "Decay and Memory Tiers"
level: intermediate
stage: evolve
estimated_minutes: 45
concepts_taught: [decay-function]
concepts_required: [salience, reinforcement, type-rules]
lessons_required: [salience-scoring]
capstone_piece: memlab.forget.decay
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Decay and Memory Tiers

> **In one line.** A single half-life applied to everything drops fourteen standing beliefs and breaks the exam — because what decays is relevance, not truth, and they differ by type.

## Where this sits

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** intermediate · **~45 min**

**You need first:** [Salience Scoring](../salience-scoring/index.md)

**Concepts assumed:** [Salience](../../../concepts/salience.md) · [Reinforcement](../../../concepts/reinforcement.md) · [Type Rules](../../../concepts/type-rules.md)

**This unlocks:** [Forgetting Under a Budget](../budgeted-forgetting/index.md)
<!-- graph:end -->

## The problem

Scoring importance once is not forgetting. A fact that mattered in March and has not been touched since should matter less now, and something has to move it out of the way.

The textbook mechanism is exponential decay on a half-life. Apply it to Priya's store with a 180-day half-life:

```
uniform      retrievable= 7  dropped=23 {semantic: 14, episodic: 7, procedural: 2}
             exam from retrievable tier: BROKEN
```

Twenty-three of thirty live memories fall out of retrieval — including **fourteen standing beliefs and both procedures** — and the system that passed the exam one lesson ago now fails it.

Look at what left: `Priya drinks tea`, `Samira is a charge nurse`, the weekly report workflow. Not one of them was contradicted. They faded because they were *said a while ago*, and `Priya does not eat meat` is exactly as true today as it was in October. **The constant is not what is wrong; the model is.**

## Why this isn't RAG

Document freshness is a real and simple signal: a 2019 page about an API is probably worse than a 2026 one, and decaying it is uncontroversial because documents *describe* a world that moves on.

Memories do not all age the same way. `Priya moved house` is over the moment it happens and recedes into history. `Priya does not eat meat` is a claim about the present that stays current until something supersedes it. One decays; the other must not. There is no equivalent distinction in a document corpus, and no single freshness curve that serves both.

## Mechanism

**Decay rate is scaled by type** — the thing `typed-memory-model` established as governing a memory's whole life.

| type | rate | why |
|---|--:|---|
| **episodic** | 1.00 | it is over; it recedes |
| **working** | 1.00 | dies with the session anyway |
| **semantic** | 0.25 | current until superseded |
| **procedural** | 0.10 | taught once, meant to outlast everything |

With that correction, the same corpus, the same half-life and the same thresholds:

```
type-scaled  retrievable=18  dropped=12 {semantic: 5, episodic: 7}
             exam from retrievable tier: CORRECT
```

Retrievable goes from 7 to 18, and the composition of what left is the real result: **every episode in the store, and only five beliefs** — against fourteen beliefs and both procedures under a uniform rate. The exam survives.

Seven of the nine live episodes fall out — the Spark job, the house move, Samira's promotion, the Northwind departures. All genuinely over. That is the rate table working, not a threshold happening to land well; if a *belief* had led that list, the rates would be wrong.

### The two episodes that stayed

One is fair: the gluten diagnosis is from May 2026 and genuinely recent.

The other is not. **`Priya used to cycle to work before the move` sits in `long_term` with `happened_at = 2026-04-08`** — the date of the *turn*, not of the cycling. Extraction never backdated it, so a memory whose own text says *"used to"* is recorded as the most recent commute fact in the store, and decay correctly concludes it is current.

Nothing downstream can repair that. Decay reads event time and event time is wrong; a ranker will make the same mistake, and so will anything else. The fix is [relative time resolution](../../advanced/relative-time-resolution/index.md) in Advanced, which parses *"before the move"* against the corpus and anchors it to August 2025.

It is worth naming rather than absorbing, because it is the shape of a whole class of bug: **a defect in a field propagates silently into every stage that trusts it.** The two-clock design from [the memory record](../../beginner/the-memory-record/index.md) made this expressible; it did not make it correct.

**Reinforcement buys back age.** Each recorded use subtracts one half-life from a memory's effective age, so something regularly recalled stops falling. Decay alone loses the rarely-mentioned-but-important; reinforcement alone keeps whatever the system happened to surface first. The pair approximates *"what has earned its place lately"*.

**Time comes from the corpus, not the clock.** `reference_now` is the newest event in the store, so the same store always yields the same salience — a test written today still passes next year, and re-running the pipeline is idempotent. Reading the wall clock here would make every stored salience a function of when the job ran, which is the non-idempotency `semantic-drift` spent a lesson on.

### Tiers

Salience is continuous; retrieval needs a decision. Three bands, deliberately wide so a memory does not oscillate across a boundary because its score moved by a hundredth:

`long_term ≥ 0.40 > working ≥ 0.20 > scratch`

Only `long_term` is retrieved by default. Nothing is removed — the log still holds all 37.

## Design decisions

**Decay salience, or decay the retrieval score?** Salience, stored. It is a property of the memory, it changes slowly, and computing it per query puts a scan on the read path for a number that barely moves. It also makes decay auditable: you can look at a memory and see what it is worth.

**One half-life with type rates, or a half-life per type?** One constant scaled by a rate table. Same expressiveness, and it keeps *"how fast does memory fade"* as a single tunable with the type differences visible beside it as a policy you can read.

**Should procedures decay at all?** Barely — 0.10 — and not zero. A workflow can genuinely be abandoned, and a type that never fades is a permanent occupant of a bounded tier. Slow enough to survive years of disuse, not so slow it is immortal.

## Lab

**You'll implement:** `decayed` with the type rate, `tier_for`, and `apply`.

**Run:**
```
uv run python curriculum/intermediate/decay-and-tiers/lab/lab.py
```

**Expected output:** the uniform pass first — **7 retrievable**, dropping fourteen beliefs — then the type-scaled one: **18 long_term, 8 working, 4 scratch**, store unchanged at 37, and the demoted list headed entirely by episodes.

**Stretch:** call `record_use` on one of the demoted episodes twice and re-run. Two uses buy back two half-lives and it returns to `long_term`. Then ask whether that is right: the system is now retrieving *"Priya moved house"* because it happened to be recalled twice, which is reinforcement doing exactly what it promises and not obviously what you want.

## What this adds to the capstone

`memlab.forget.decay` — `DECAY_RATE`, `decayed`, `tier_for`, `apply`, `reference_now`. The `intermediate` profile switches on `decay`, which runs salience → decay → budget after consolidation.

**This flips the sixth pinned failure.** `test_forgetting` now asserts that salience discriminates and something is demoted — and, still, that nothing has been removed from the log.

**Summarization stays off.** [Compaction](../summarization-and-compaction/index.md) was built and left unwired pending budget pressure, and the next lesson shows the bound does not yet bind at 37 memories. Running a lossy transform for a budget nothing is exceeding is a cost with no benefit; it turns on when the cap does.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| The store empties | One decay rate for every type | Count retrievable memories after a decay pass | Scale the rate by type |
| Standing facts fade | Semantic decay too fast | Check whether an unsuperseded belief left the tier | Low rate for claims about the present |
| Salience depends on when the job ran | Decay reads the wall clock | Run the pass twice; diff | Reference time from the corpus |
| Memories flip tiers constantly | Bands too narrow | Watch a memory near a boundary | Wide bands |
| Only what was surfaced before survives | Reinforcement dominating | Test a fact stated once and never queried | Cap the age reinforcement can buy back |

## Check yourself

??? question "The uniform version dropped fourteen beliefs. Why is that a modelling error rather than a bad constant?"
    Because no constant fixes it. Slow the decay enough to keep beliefs and episodes never fade either, so the store grows without bound; speed it up and beliefs die. The two need different curves, and one number cannot express two curves. That is a model problem wearing a tuning problem's clothes.

??? question "Type-scaled decay still drops five beliefs. Is that acceptable?"
    It is the point, not a leak — forgetting has to forget something. What matters is *which*: the five are low-salience filler like `Priya mostly does pipeline work`, and the exam still answers correctly from what remains. The next lesson shows how narrow that margin actually is.

??? question "Why take 'now' from the corpus instead of the clock?"
    So the pass is idempotent and its results reproducible. With wall-clock time, every stored salience becomes a function of when the job happened to run, two runs an hour apart disagree, and no test can pin the result — the same failure `semantic-drift` identified in compaction.

## Connections

<!-- graph:begin -->
**Stage:** `evolve` · **Level:** intermediate · **~45 min**

**You need first:** [Salience Scoring](../salience-scoring/index.md)

**Concepts assumed:** [Salience](../../../concepts/salience.md) · [Reinforcement](../../../concepts/reinforcement.md) · [Type Rules](../../../concepts/type-rules.md)

**This unlocks:** [Forgetting Under a Budget](../budgeted-forgetting/index.md)
<!-- graph:end -->
