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

## Status

**Milestone 1 complete.** Scaffold, validator suite, the 84-lesson syllabus, all
13 Beginner lessons with labs, 28 concept pages, and `memlab` v0.1 (extract →
store → retrieve → assemble, with a CLI). 100 tests pass; all 8 validators pass.

`capstone/tests/test_v1_failures.py` pins the seven ways v0.1 is broken. Those
tests are the baseline every Level 2 claim is measured against — when a level-2
mechanism fixes one, move its test and flip the expectation rather than deleting it.

Landscape snapshot written and dated 2026-08-27 (8 pages; high-volatility pages
fail CI at 180 days — re-verify rather than bumping the date).

**Milestone 2a complete** — Intermediate modules I1–I4 (15 lessons), 45 concept
pages, `memlab` v0.2-alpha. 238 tests.

The headline result: the session-14 exam passes under `--profile intermediate`
and fails under every earlier snapshot. `uv run python -m memlab.app.chat
--profile intermediate --ingest --exam`.

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

Remaining: Intermediate I5–I8 (16 lessons — forgetting, retrieval, stores,
assembly), Advanced (40), and `mkdocs.yml` (Phase 7 — the CI step is present
but gated on the file existing).
