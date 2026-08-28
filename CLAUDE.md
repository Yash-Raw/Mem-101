# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A hands-on curriculum for building an **agent memory layer** — 84 lessons across
three levels, each with a runnable Python lab, plus one capstone system
(`memlab`) that grows across the whole course.

It is a content repo with executable parts, not an application. The product is
`curriculum/` and `concepts/`; `capstone/` exists to be built by the learner.

## Commands

```bash
uv sync --dev                       # set up (Python 3.11+; system python3 is 3.9, always use uv run)
uv run python tools/check.py        # the full validator suite — run before every commit
uv run pytest -q                    # every lab + capstone tests
uv run pytest curriculum/beginner/memory-is-not-rag/lab/ -q   # a single lab
uv run ruff check .                 # lint

uv run python tools/render_syllabus.py   # regenerate SYLLABUS.md after editing syllabus.yml
uv run python tools/build_graph.py       # regenerate graph blocks + concepts/graph.json
```

Both generators take `--check` (used by CI) to fail on stale output instead of rewriting.

`MEMLAB_LLM` selects the backend: `fake` (default, no API key) or `anthropic`.

## The thesis, which is load-bearing

RAG is a **read path over a corpus someone else wrote**. A memory layer is
dominated by the **write path**: extraction, entity resolution, conflict
detection, belief updating, consolidation, decay. Roughly half the course sits
in `evolve` and `govern`; only ~11% is `retrieve`.

Every lesson has a mandatory `## Why this isn't RAG` section. If a change makes
that section feel redundant, the change is probably wrong.

## Architecture

**Ordering vs. dependency are two different things, stored separately.**
`curriculum/syllabus.yml` is the single source of truth for *linear order*.
The *prerequisite DAG* lives in each lesson's frontmatter (`lessons_required`,
`concepts_required`). `tools/validate_graph.py` proves the linear order is a
valid topological sort of the DAG — that check is what makes the level split a
guarantee rather than an intention. Reordering the course means editing one
YAML list; `SYLLABUS.md` is generated and must never be hand-edited.

**`curriculum/` teaches; `concepts/` defines.** A concept has exactly one home
page, linked from everywhere it appears. Concept pages carry `contrasts_with`
to name the idea they get confused with. Frontmatter fields `taught_in` and
`used_in_capstone` are *derived* — hand-authoring them is a validation error.

**`landscape/` is a quarantine.** No product name, vendor, or benchmark number
may appear in `curriculum/` or `concepts/` except inside a
`<!-- landscape:begin -->…<!-- landscape:end -->` block. Enforced against
`landscape/registry.yml`. Pages there carry `last_verified` and fail CI once
stale (180 days at `volatility: high`). The conceptual spine must survive any
named tool being renamed or abandoned.

**Generated regions** are delimited by `<!-- graph:begin -->` / `<!-- graph:end -->`
and are rewritten by `build_graph.py`. Never edit inside them.

**One canonical corpus.** `capstone/fixtures/corpus.jsonl` — Priya, 14 sessions,
Mar 2025 → Aug 2026 — is used by *every* lab at *every* level, with ground truth
in `gold.yml`. It is deliberately seeded with a job change, entity aliases, a
diet chain (refinement + addition), a genuine contradiction, relative time
references, PII plus a deletion request, a taught procedure, and low-authority
hearsay from another agent. When writing a lesson, cite this corpus rather than
inventing an example — the continuity is the point.

**`memlab` is one codebase with level profiles**, not three copies. A lab stubs
one named function inside a working system; `--profile beginner|intermediate|advanced`
disables later machinery. Each lesson's `capstone_piece` is a dotted path that
`validate_capstone.py` actually imports, so content and code cannot drift apart.

## Conventions that CI enforces

- **C1** Directory names are stable, number-free slugs. Ordering is data.
- **C4** A lesson's `id` equals its directory name; a concept's `id` equals its filename.
- **C5** Cross-links are relative and end in `.md` — the only form that works both on GitHub and in the built site. Absolute links fail.
- **C7** Labs are `.py`, never notebooks. Each declares `lab.py` + `solution.py` + `test_lab.py`.
- Lessons must contain the ten `##` sections in order (see `LESSON_SECTIONS` in `tools/validate_frontmatter.py`). `Failure modes` needs ≥2 table rows.

A link to a lesson listed in `syllabus.yml` but not yet authored is a *forward
reference*, reported as a note rather than a failure — authoring is incremental.

## Writing labs

Labs must run offline, in CI, with no API key. `memlab.llm.fake.FakeLLM`
provides deterministic hashed-n-gram embeddings that are genuinely responsive to
wording (near-paraphrase ≈0.79, unrelated ≈0.07), so retrieval labs teach real
behaviour. It is a *lexical* model, and that limit is itself teaching material.

Completions are fixture-backed. Author fixtures with
`memlab.llm.fake.register_fixture(messages, response, schema)` — it computes the
lookup key and writes JSON, with no model call, so fixtures stay reviewable in a diff.

Prefer asserting the *exact* documented output; determinism is what makes that possible.

**Never `import solution` or `import lab` by bare name in a test.** Every lab
ships modules with those names, and a bare import resolves to whichever landed
in `sys.modules` first — so the second lab collected gets the first lab's code,
silently. Use the loader instead, which namespaces by lesson:

```python
from memlab import labkit

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)

retrieve_topk = _solution.retrieve_topk
```

`tools/validate_structure.py` fails the build on bare imports or `sys.path`
manipulation inside a test.

## Level profiles and module snapshots

`memlab.pipeline` decides which stages run. `get("beginner")` is Level 1 as
shipped; `get("intermediate")` is everything built so far; **`at("I3")` is the
system as module I3 left it.**

Snapshots exist because lesson prose quotes measured numbers. I3's dedupe
changes the store size, which would silently invalidate every count I1 quoted.
So a lesson's tests pin against its own module's snapshot, and a number
measured once stays true. When adding a module, extend `MODULES` and switch on
exactly one capability, so its claimed improvement is attributable to it alone.

## Verifying prose against reality

`tools/validate_expected_output.py` runs **every lab** with its reference
solution patched over the stubs, then checks that each figure quoted in the
lesson's measuring sections appears in what the lab actually printed — or is
pinned in that lab's test file.

It exists because a grep-based staleness sweep passed while seven figures across
five lessons were wrong: three I3 lessons had been re-pointed to a different
pipeline snapshot without re-measuring, and "25 turns → 36 memories" was wrong
in seven places (session 14 is held out, so it is 24). Sampling is not
verification. **When a lesson's number changes, re-run the lab — never edit the
number to match a memory of what it used to be.**

## Status

**Milestone 1 complete.** Scaffold, validator suite, the 84-lesson syllabus, all
13 Beginner lessons with labs, 28 concept pages, and `memlab` v0.1 (extract →
store → retrieve → assemble, with a CLI).

`capstone/tests/test_v1_failures.py` pins the seven ways v0.1 is broken. Those
tests are the baseline every Level 2 claim is measured against — when a level-2
mechanism fixes one, move its test and flip the expectation rather than deleting it.

Landscape snapshot written and dated 2026-08-27 (8 pages; high-volatility pages
fail CI at 180 days — re-verify rather than bumping the date).

**The Intermediate level is complete** — I1–I8, 31 lessons, `memlab` v0.2.
395 tests.

Three headline results, each with its own passing snapshot:

| exam | question | passes from |
|---|---|---|
| **belief** | does the store *believe* the right thing? | `@I4` |
| **context** (k=5) | would the model ever *say* it? | `@I6` |
| **budgeted** (52 tokens) | does it survive a tight context? | `@I8` |

```
uv run python -m memlab.app.chat --profile intermediate --ingest --exam --budget 52
```

Correct at 52 and wrong at 50. The derived floor — a compact header plus the
four required facts — is 43; the nine-token gap is one memory the packer has no
information to reject.

Two findings that shaped the design, both from measurement rather than
reasoning — worth knowing before extending this:

- **Similarity cannot generate conflict candidates.** The employer
  contradiction scores 0.285, below unrelated noise at 0.478. Candidates are
  grouped by `SLOT` (the attribute claimed) instead. Removing a slot silently
  reverts the exam.
- **Similarity cannot identify corroboration either.** A refinement scores
  0.669, a genuine corroboration 0.505, a contradiction 0.439. No threshold
  separates them, which is why `evolve/promote.py` promotes nothing and defers
  to conflict detection.

Two more findings from 2b, both of which reversed an obvious approach:

- **Salience must not be added to a relevance score.** It moves the correct
  answer *down* and promotes a taught procedure to first place. Importance and
  relevance are different axes; salience is for forgetting, and only earns a
  ranking term alongside type and slot.
- **Decay rate must be scaled by memory type.** One half-life for everything
  drops fourteen standing beliefs and breaks the exam. What decays is
  relevance, not truth.

Two from 2c, both of which are null results a lesson is built on:

- **This corpus has one graph node and no edges.** `samira`, six memories;
  `St. Aubyn's` is on the stop list. `graph-stores` teaches when a graph earns
  its cost by measuring a corpus where it does not.
- **Three of I8's four mechanisms move nothing.** Reservation, padding
  suppression and pinning are each correct and each a no-op here; the only
  lever is that the framing header was 38% of the context. Optimise the
  elements you priced, not the ones you assumed mattered.

**Milestone 3a complete** — Advanced modules A1–A2 (9 lessons), `memlab`
v0.3-alpha. 520 tests.

```
uv run python -m memlab.app.chat --profile advanced --ingest --exam --budget 51
```

Correct at 51, wrong at 50. (`slot-value` reports 52 because its sweep tested
discrete budgets and never tried 51 — both pass.)

Level 3 layers on top of Level 2 rather than replacing it: `advanced("A1")` is
`intermediate("latest")` plus A1's switches, `ADVANCED_MODULES` runs A1–A9, and
`at()` dispatches on the prefix so `at("I3")` and `at("A1")` both mean "as that
module left it". A1 carries two switches (`bitemporal`, `anchor`) against the
one-per-module convention; a lesson needing a sub-state pins it explicitly with
`at("A1").with_stage(anchor=None, ...)`.

**`uv run python tools/dump_snapshots.py`** is the before/after proof for every
shared-code change. It covers `@I1`–`@I8` *and* the landed `@A*`, plus
`valid_from` / `valid_to` / distinct `recorded_at` / every event time — the
fields A1 added, which an ids-and-scores dump would not have caught moving.

Three shared-code changes landed under Level 2, all proven snapshot-safe and
none visible from lesson prose: `recorded_at` now comes from the turn clock in
both extract paths (v0.2 records are **deterministic between runs**, which they
were not); `evolve/promote.py` writes memory ids into `derived_from` rather than
source ids, matching `summarize`; and `retrieve.scoped.eligible`/`search` gained
`live_only` and `retrievable_only`, both defaulting to today's behaviour.

Findings from 3a, each a lesson's spine:

- **Two clocks in the record, and neither read the sentence.** 37 of 37 event
  times were the instant the record was written. The first audit reported 34/37
  by counting only user turns — agent writes stamp their own clock too, so a
  denominator chosen without checking turned a 100% failure into 92%.
- **`invalid_at` was answering two questions**, retiring the Berlin hearsay nine
  months before it was recorded. `valid_to` is when a fact stopped being true;
  `invalid_at` is when the store found out.
- **The read path assumed *now* in three places.** Routing a dated question
  fixes nothing until both `live_only` and the I5 tier cap are released: 0 → 0 →
  1 → 4 of 4. A memory demoted for being stale is the memory a question about
  the past wants.
- **A relative-time parser must be able to decline.** Four classes of phrase and
  the fifth answer is "not a time reference" — `diff against last week` is a
  step inside a taught procedure, and resolving it dates the recipe.
- **Deferred consolidation costs the window, not the compute.** 13× cheaper,
  identical store, and 11 of 24 turns believing a job she had already left. The
  gate that closes it is `slot_of` — already computed by the write path.
- **`store.replace(consolidate(store.all()))` destroys 33 memories** when a turn
  lands mid-job, worst case the whole session-8 job change. A write-back must
  record *which ids* it read: absence means both "merged away" and "never seen".
- **Reflection derives three correct beliefs and every way of storing them is
  worse** — lowest passing budget 51 → 55 joined, → 56 replacing. The packer
  selects memories, so composition destroys its ability to drop what the
  question does not need. Ships unwired, like `promote()`.

Remaining: Advanced A3–A9 (31 lessons), and `mkdocs.yml` (Phase 7 — the CI step
is present but gated on the file existing).
