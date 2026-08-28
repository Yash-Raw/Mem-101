---
id: failure-class
title: "Failure Class"
kind: concept
stage: govern
contrasts_with: [differential-diagnosis]
related: [consistency-window, unnameable-claim, cascade-deletion]
status: published
---

# Failure Class

A production problem named by what the user sees, not by which component is wrong.

## Why it matters in a memory layer

A retrieval failure is usually diagnosable from one artifact — the ranked list. The document is missing or it is ranked low, and either way *"why didn't it come back?"* is answered by inspecting one thing.

Here the same symptom arrives from different stages. *"A fact I told you is never recalled"* has three causes — never extracted, extracted but **unnameable** so never arbitrated, or demoted out of the retrievable tier — living in three modules, and the store looks identical from the outside in all three. **The read path is the last place to look, and the only place a retrieval intuition suggests looking.**

Five of the seven classes in this course's guide have more than one cause. Organise by symptom, because the symptom is what arrives; a stage-indexed taxonomy is only usable by someone who already knows the answer.

## Connections

<!-- graph:begin -->
**Taught in:** [The Failure Field Guide](../curriculum/advanced/failure-field-guide/index.md)

**Do not confuse with:** [Differential Diagnosis](differential-diagnosis.md)
<!-- graph:end -->
