---
id: reading-list
title: "Reading List"
kind: landscape
category: paper
volatility: medium
last_verified: 2026-08-27
verified_by: "course maintainers"
claims_are_vendor_sourced: false
maps_to_concepts: [memory-lifecycle, belief-updating, bi-temporal-modeling]
---

# Reading List

!!! warning "Dated snapshot — verified 2026-08-27"
    Primary sources age better than tool pages, but the frontier moves. Where a
    survey is superseded, prefer the newer one.

Papers, not products. Read the surveys first — they are the cheapest way to get
a map — then follow their citations into whichever stage you are working on.

## Start here: surveys

- **Memory in the Age of AI Agents** (arXiv 2512.13564) — the broad map, and the
  source of the extract → store → retrieve → evolve framing this course uses.
  Accompanied by a maintained paper list at
  [Shichun-Liu/Agent-Memory-Paper-List](https://github.com/Shichun-Liu/Agent-Memory-Paper-List).
- **Rethinking Memory Mechanisms of Foundation Agents in the Second Half**
  (arXiv 2602.06052) — a more opinionated survey; good on open problems.
- **Always-On Agents: Persistent Memory, State, and Governance in LLM Agents**
  (arXiv 2606.30306) — the governance side, including why deletion has to cascade.
- **AI Meets Brain: Memory Systems from Cognitive Neuroscience to Autonomous
  Agents** (arXiv 2512.23343) — read it for where the biological analogy
  genuinely constrains design, and where it is decoration.

## The write path

- **Belief Memory: Agent Memory Under Partial Observability** (arXiv 2605.05583) —
  treating stored facts as beliefs with confidence rather than assertions.
- **When Does Belief-Based Agent Memory Help? Reliability-Conditional Updating
  and Provenance-Capped Poisoning Defense** (arXiv 2606.22030) — the paper to
  read before designing an update rule; also the clearest treatment of why
  provenance is a security control.
- **Less Context, More Accuracy: A Bi-Temporal Memory Engine for LLM Agents**
  (arXiv 2606.09900) — bi-temporal modelling with an empirical case that a lean
  retrieved context beats full history.

## Evolution, consolidation, forgetting

- **Control-Plane Placement Shapes Forgetting: An Architectural Study of Agent
  Memory Across Thirteen System Configurations** (arXiv 2606.15903) — *where* the
  forgetting decision lives changes what gets forgotten.
- **Governing Evolving Memory in LLM Agents: Risks, Mechanisms, and the Stability
  and Safety Governed Memory (SSGM) Framework** (arXiv 2603.11768) — drift,
  runaway self-reinforcement, and decay functions.
- **How Memory Management Impacts LLM Agents: An Empirical Study of
  Experience-Following Behavior** (arXiv 2505.16067) — what actually happens as
  stored experience accumulates.

## Deletion and privacy

- **Agentic Unlearning: When LLM Agent Meets Machine Unlearning**
  (arXiv 2602.17692) — introduces *information backflow*: parametric residue
  regenerating a "forgotten" fact, which is then written back to memory,
  reversing the deletion. Read before you believe a deletion is complete.
- **MEMOREPAIR: Barrier-First Cascade Repair in Agentic Memory**
  (arXiv 2605.07242) — repairing derived artifacts after a deletion.
- **Forgetful but Faithful: A Cognitive Memory Architecture and Benchmark for
  Privacy-Aware Generative Agents** (arXiv 2512.12856).

## Evaluation

- **LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced
  Colleagues** (arXiv 2605.12493).
- **StreamMemBench** (arXiv 2606.14571) — streaming evaluation, closer to how a
  deployed system is actually exercised.
- **ImplicitMemBench** (arXiv 2604.08064) — measures unconscious behavioural
  adaptation, i.e. whether memory changed behaviour rather than recall.

## How to read this literature

Three habits worth adopting. Check whether a paper evaluates the **write path**
or only recall — most measure recall and claim memory. Check whether reported
gains survive a change of backing model. And check the contradiction handling
specifically: a system can look excellent on every benchmark here and still
never retire a stale fact, because most benchmarks do not ask.
