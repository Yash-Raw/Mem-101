---
id: hybrid-ranking
title: "Hybrid Ranking"
level: intermediate
stage: retrieve
estimated_minutes: 55
concepts_taught: [hybrid-ranking, score-fusion]
concepts_required: [vector-search, salience, slot, type-rules, canonical-entity]
lessons_required: [scope-then-rank]
capstone_piece: memlab.retrieve.hybrid
lab: lab/lab.py
lab_runtime: fake
status: published
---

# Hybrid Ranking

> **In one line.** Six signals instead of one takes the correct answer from rank 12 to rank 2 — and the decisive one finds facts that share no vocabulary at all with the question.

## Where this sits

<!-- graph:begin -->
**Stage:** `retrieve` · **Level:** intermediate · **~55 min**

**You need first:** [Scope, Then Rank](../scope-then-rank/index.md)

**Concepts assumed:** [Vector Search](../../../concepts/vector-search.md) · [Salience](../../../concepts/salience.md) · [Slot](../../../concepts/slot.md) · [Type Rules](../../../concepts/type-rules.md) · [Canonical Entity](../../../concepts/canonical-entity.md)

**This unlocks:** [The Query Is Not the Last Message](../query-formulation/index.md)
<!-- graph:end -->

## The problem

Filtering got the employer to rank 12 of 18. The remaining competition:

```
0.312  Priya does not eat meat
0.232  Priya's weekly report process: pull pipeline metrics ...
0.221  Priya used to cycle to work before the move
0.191  Priya was diagnosed with a gluten intolerance last week
0.137  Priya's new role involves more architecture and less firefighting
```

Cosine is doing its job and its job is not enough. Every one of these is *about Priya* and *mentions something plausible*, and similarity has no way to prefer a current employment fact over a workflow, a past commute, or an aside about her new role.

Meanwhile the store knows six other things about each memory — when it was true, how much it matters, what type it is, who it is about, what attribute it fills — every one recorded by an earlier module, and none consulted.

## Why this isn't RAG

Hybrid retrieval over documents means BM25 plus embeddings: two ways of measuring the same thing, textual aboutness, to cover each other's blind spots.

Here the signals are **categorically different**, and most of them are not about text at all. Recency is a fact about the world. Salience is a fact about the memory's history. Type and slot are facts about what *kind* of claim it is. Fusing them is not covering a blind spot in similarity; it is asking questions similarity cannot express.

## Mechanism

Six terms. The weights matter and none of them were reasoned out.

| signal | weight | question it answers | from |
|---|--:|---|---|
| similarity | 1.00 | what is this about? | Beginner |
| **slot** | **0.60** | does it fill the attribute asked about? | **I4** |
| coverage | 0.50 | how much of the question's vocabulary is here? | this module |
| type | 0.50 | does this *shape* of memory answer this *shape* of question? | I1 |
| subject | 0.40 | is it about the right person? | I2 |
| recency | 0.20 | when was it true? | Beginner |
| salience | 0.15 | how much does it matter? | I5 |

**Slot is the strongest, and it is the one that does something similarity cannot.** `Priya has a gluten intolerance` and *"what should I not eat"* share **no words**: coverage is near zero and similarity is weak, so the fact ranked 10th. Slot membership is set lookup — the `SLOTS` table from [contradiction detection](../contradiction-detection/index.md), written for the *write* path to group conflicting beliefs, reused here to find relevant ones. One vocabulary, two consumers.

**Coverage, not Jaccard.** The first version used Jaccard and `Priya works at Calico Systems` lost to `Sam still works nights` — purely because Jaccard divides by the union and the correct memory was longer. Coverage asks what fraction of the *question's* terms appear, and ignores whatever else the memory says.

**Light stemming, because `work` ≠ `works`.** Without it, a query about employment scores zero lexical overlap against the memory that answers it. Unglamorous, and it is the difference between the term signal working and not.

**Type as preference, and the weight was swept.** `AFFINITY` maps question shape to memory type: a `STATE` question prefers semantic memories, a `PROCEDURE` question prefers procedural ones. At weight 0.30 the past-tense commute episode still ranked 2nd; at 0.50 it dropped out. That number came from a sweep, not from judgement.

**Subject, because `Sam still works nights` is a fine memory and answers nothing Priya asked about herself.** It survives similarity, coverage and recency on the strength of one shared word.

### What it does

Employer rank **12 → 2 of 18**, with the procedure and the episodes gone from the top.

The per-signal breakdown for that memory is worth reading closely:

```
slot         0.600
type         0.500
subject      0.400
coverage     0.250
recency      0.157
salience     0.064
similarity   0.054   <- the smallest contributor
```

**Similarity contributes least to finding the right answer.** `Priya works at Calico Systems` barely resembles *"where do I work and what should I not eat?"* as text — it is found because it fills the right slot, is the right type, is about the right person, and is recent. Five modules of write-path work, finally being read.

And this is where [salience scoring](../salience-scoring/index.md)'s finding gets resolved. There, adding salience to a plain relevance score pushed the correct answer *down* two places and put a taught procedure first. Here salience sits at weight 0.15 *alongside* type and slot — and the procedure it promotes is held down by a type term that knows a workflow does not answer a factual question. **The signal was never wrong; it was unusable alone.**

## Design decisions

**Linear weights or a learned model?** Linear. Every term is inspectable, `Scored.parts` shows exactly why a memory ranked where it did, and a user asking *"why did you tell me that?"* gets an answer. A learned ranker needs labels nobody has and explains nothing.

**Should type be a filter rather than a weight?** A weight. `AFFINITY` sets episodic to 0.0 for a `STATE` question, which is a strong preference and not a ban — because *"when did I change jobs"* is a state-shaped question with an episodic answer, and a filter would make it unanswerable.

**Why is similarity still the largest single weight?** Because it is the only term that generalises. Slot, type and subject depend on tables and fields that can be missing or wrong; similarity works on anything. The others *re-rank* a relevance signal rather than replacing it.

## Lab

**You'll implement:** `coverage`, `subject_match`, `slot_match`, and `score_one`.

**Run:**
```
uv run python curriculum/intermediate/hybrid-ranking/lab/lab.py
```

**Expected output:** employer at rank **2 of 18**, the per-signal breakdown for the top results, and the type-weight sweep showing the commute episode dropping out between 0.30 and 0.50.

**Stretch:** set `W_SLOT` to 0 and re-rank the compound question. The gluten fact falls from **rank 5 to rank 9** — out of a five-slot context.

Then ask the diet half on its own and watch the term stop mattering: `what should Priya not eat?` reaches the gluten fact at rank 3 either way, because the user's own name is enough vocabulary once the question is not diluted. **Slot earns its weight precisely where the query is vague**, which is where real questions live.

## What this adds to the capstone

`memlab.retrieve.hybrid` — `score_one`, `rank`, `coverage`, `terms`, `subject_match`, `slot_match`, `intent_of`, `AFFINITY`, and the weight table.

## Failure modes

| Symptom | Cause | How to detect | Mitigation |
|---|---|---|---|
| Facts that answer the question never surface | No slot term; question and fact share no words | Ask something whose answer uses different vocabulary | Slot membership |
| Long correct memories lose to short wrong ones | Jaccard-style length normalisation | Compare scores of the same fact at two lengths | Coverage over the query |
| A query about employment misses `works at` | No stemming | Check the lexical term on a known match | Normalise terms |
| Another person's memories answer your question | No subject term | Ask a first-person question about a shared topic | Subject match on entities |
| Procedures surface for factual questions | Salience without type affinity | Sweep the type weight and watch what leaves | Type affinity |
| Nobody can explain a ranking | Fused score with no breakdown | Ask why a memory ranked 4th | Keep per-signal parts |

## Check yourself

??? question "Salience made ranking worse two lessons ago and helps here. What changed?"
    The company it keeps. Alone, salience promotes whatever is most important in general — the taught procedure. Alongside a type term that knows a procedure does not answer a factual question, its contribution is confined to breaking ties among memories that were already the right shape. A signal is not good or bad on its own; it is good or bad in a model.

??? question "Slot is the highest-weighted term. Doesn't that make the ranker dependent on a hand-written table?"
    Yes, and that dependency is why similarity keeps the largest single weight. Slot is decisive when the table covers the domain and contributes nothing when it does not, which is exactly the behaviour you want from a high-precision, low-coverage signal: strong when it fires, harmless when it does not.

??? question "Similarity contributes 0.054 to the correct answer. Why keep it weighted at 1.00?"
    Because its weight is not its contribution. Similarity scores *everything* in the pool, so a 1.00 weight on a small value still separates memories the categorical signals cannot distinguish — and it is the only term that works when the slot table has no entry, the entities are unresolved, or the type is wrong. It earns its weight on the queries this one happens not to need it for.

??? question "The type weight came from a sweep. Is that not overfitting to one corpus?"
    It is fitted to one corpus, and the honest response is to say so. What the sweep establishes is that 0.30 was too low to move a known-wrong result and 0.50 was enough — a direction and a rough magnitude, not a universal constant. Any new corpus needs the sweep repeated, which is why the lab is the sweep rather than the number.

## Connections

<!-- graph:begin -->
**Stage:** `retrieve` · **Level:** intermediate · **~55 min**

**You need first:** [Scope, Then Rank](../scope-then-rank/index.md)

**Concepts assumed:** [Vector Search](../../../concepts/vector-search.md) · [Salience](../../../concepts/salience.md) · [Slot](../../../concepts/slot.md) · [Type Rules](../../../concepts/type-rules.md) · [Canonical Entity](../../../concepts/canonical-entity.md)

**This unlocks:** [The Query Is Not the Last Message](../query-formulation/index.md)
<!-- graph:end -->
