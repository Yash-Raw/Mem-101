---
id: landscape-index
title: "The Landscape"
kind: landscape
category: vendor-claim
volatility: high
last_verified: 2026-08-27
verified_by: "course maintainers"
---

# The Landscape

Everything in this directory has a shelf life. Everything outside it does not.

The lessons in `curriculum/` and the definitions in `concepts/` never name a
product, a vendor, or a benchmark score. That is enforced by
`tools/validate_quarantine.py`, not by good intentions: a build fails if a name
from `registry.yml` appears in the conceptual spine outside a marked block.

## Why the wall exists

While researching this course, the same memory system was found cited at two
very different scores on the same benchmark suite — one figure from an
independent comparison, one from the vendor's own blog. Neither was flagged as
contested. Both were published within months of each other.

That is not unusual, and it is not necessarily dishonest. Benchmark numbers
depend on the backing model, the retrieval budget, the prompt, and which subset
was run. But it means a number quoted without its conditions is close to
meaningless, and a number embedded in a lesson is a number that will be wrong
by the time someone reads it.

So the rule is: **the mechanism goes in the lesson; the vendor goes here, dated.**
A learner who understands supersession can evaluate any system that claims to do
it. A learner who memorised a leaderboard row has learned something with a
half-life of weeks.

## How to read anything in this directory

- Check `last_verified` before trusting a page. High-volatility pages fail CI at
  180 days precisely so they cannot rot silently.
- Treat `claims_are_vendor_sourced: true` as "this is marketing until reproduced."
- Run the numbers yourself where it matters. The eval harness built in
  [end-to-end eval](../curriculum/advanced/end-to-end-eval/index.md) scores any
  system against the same corpus this course teaches from, which is a more
  useful comparison than a leaderboard you did not run.

## Contents

Pages land here as the course reaches the modules that reference them:

- `tools/` — how shipping systems structure extraction, storage, and conflict resolution
- `benchmarks/` — what each public memory benchmark actually measures, and what it misses
- `standards/` — proposed portability and interop work, and how far to trust it
- `papers/reading-list.md` — the surveys and primary sources worth reading directly
