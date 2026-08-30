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
uv run python tools/build_site_data.py   # regenerate docs/assets/data/site.json + the home hero
uv run python tools/render_nav.py        # regenerate mkdocs' nav from syllabus.yml
```

Every generator takes `--check` (used by CI) to fail on stale output instead of rewriting.

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
wording (measured: near-paraphrase 0.69-0.82, unrelated 0.02-0.04), so retrieval
labs teach real behaviour. It is a *lexical* model, and that limit is itself teaching material.

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

**The course is complete and published.** 84 lessons across three levels, 823
tests, eight validators and four generated-file checks, `memlab` v0.3. Public at
[github.com/Yash-Raw/Mem-101](https://github.com/Yash-Raw/Mem-101), site at
<https://yash-raw.github.io/Mem-101/>, deployed by CI from `main` only after
`check` is green — the site is never newer than the validators that vouch for
it. The site carries a generated home hero, a filterable course map at `/map/`
and a concept atlas at `/atlas/`. Dual licence: CC BY 4.0 on prose, MIT on code.

`tools/show.py <lesson-id>` prints what a lab produces when solved. It exists
because a clean-clone test found the README's first command was `lab.py`
itself, which raises `NotImplementedError` by design — the "run it yourself"
promise opened with a traceback and no test could catch it, since the stub
raising is what `test_stub_is_runnable` asserts. It reuses
`validate_expected_output.lab_output`, so learner and CI share one code path.

```
uv run python -m memlab.app.chat --profile advanced --ingest --exam --budget 51
```

Three exams, each with its own passing snapshot, and each answering a
different question:

| exam | question | passes from |
|---|---|---|
| **belief** | does the store *believe* the right thing? | `@I4` |
| **context** (k=5) | would the model ever *say* it? | `@I6` |
| **budgeted** | does it survive a tight context? | `@I8`, at 51 tokens |

`capstone/tests/test_advanced_targets.py` holds Level 3's targets the way
`test_v1_failures.py` holds Beginner's: assert what is broken, gate the
expectation on a pipeline capability, and let the module that fixes it flip
its own test.

## Architecture added in Level 3

`advanced(through=...)` layers on `intermediate("latest")`; `ADVANCED_MODULES`
runs A1–A9; `at()` dispatches on the prefix, so `at("I3")` and `at("A1")` both
mean "as that module left it". A1 carries two switches (`bitemporal`,
`anchor`) against the one-per-module convention — a lesson needing a sub-state
pins it explicitly with `at("A1").with_stage(anchor=None, ...)` **and says so
in its own Design decisions**, because a stale column label there was one of
three seams a cold read caught.

**`uv run python tools/dump_snapshots.py`** is the before/after proof for every
shared-code change. Extend its `LANDED` tuple in the same commit as the module
— during A2 it still said `("A1",)`, so four lessons' worth of "snapshots
UNCHANGED" was silent about `@A2`.

`tools/render_nav.py` generates mkdocs' nav from `syllabus.yml`. Ordering has
one source of truth and the site is its third view, after `SYLLABUS.md` and the
prerequisite graph.

## The site is the fourth view

`tools/build_site_data.py` writes two things and both are checked: an
`assets/data/site.json` that the **course map** (`map.md`) and the **concept
atlas** (`atlas.md`) render at runtime, and a generated Jinja partial the home
page includes at *build* time. The hero is a partial rather than a fetch
because its job is to show the thesis -- half the course is `evolve` and
`govern`, a ninth is `retrieve` -- and a figure that arrives after paint, or
not at all without JavaScript, is not showing it. No number on the site is
typed; that is the same rule as the lesson prose, applied to templates.

Three things about it that were each found the hard way:

- **The atlas does not draw the prerequisite graph, and must not.** All 83
  `requires_lesson` edges form one chain identical to reading order, so it
  renders an 84-node snake. What branches is lesson<->concept.
- **Material stamps `data-md-color-scheme` on `<body>`, not `<html>`.** A
  custom property resolves `var()` against the element it is *declared* on, so
  a palette derived on `:root` mixes from the light literals in both themes.
  `docs/assets/css/mem101.css` declares the derivations wherever the literals
  are; moving them back silently breaks dark mode.
- **`var()` does not resolve in SVG presentation attributes.** `fill="var(--x)"`
  falls back to the initial value -- black fill, no stroke. Colour in the atlas
  goes through `style`.

Site scripts derive their URLs from their own `src`, never from the site root:
the published site is served from `/Mem-101/`, so a root-absolute fetch works
under `mkdocs serve` and 404s in production. That is C5 applied to JavaScript.

## Sequence, and why it lives in the template

The course is one line -- 83 prerequisite edges, every one in-degree and
out-degree 1 -- but the site presented it as a library, and a first-time
learner said so. The fix was structure around the content, under a constraint
worth keeping: **`git diff --stat curriculum/ concepts/` must stay empty.**

That constraint is what puts the per-lesson furniture in `overrides/main.html`
rather than in `build_graph.py`'s blocks, which are written *into* lesson
markdown. `build_site_data.py` emits a second generated partial,
`partials/lesson-strip.html` -- a Jinja lookup keyed by `page.file.src_uri`
carrying position, module, minutes and the lab command. Build-time, like the
hero: "lesson 7 of 84" has to survive JavaScript being off.

Three things measured here that are easy to get wrong again:

- **`navigation.prune` alone does nothing for the concept index.**
  `navigation.sections` renders top-level groups fully expanded, so all 132
  concept links shipped on every lesson page. Dropping `sections` took the
  sidebar from 242 links and 115 KB to 19 links and 12 KB.
- **A section index page must literally be named `index.md`.** Material keys
  `navigation.indexes` off mkdocs' `File.is_index`, so `modules/foundations.md`
  was ignored and `modules/foundations/index.md` works. That is why the 21
  generated module pages are directory index pages.
- **Nav order *is* prev/next.** `Contributing` sits below the generated block
  because whatever is directly above it becomes lesson 1's "previous". The one
  seam left: the final lesson's "next" is the first concept page, since
  `render_nav.py` appends Concepts after the levels.

`docs/assets/js/progress.js` is per-viewer only -- a localStorage list of
finished lesson ids behind the strip's button, and a "continue" line on the
home page. No displayed figure is ever derived from it.

## What the course established

Three claims survived every measurement, and none was obvious at the start.

- **The write path dominates.** 2.0 model calls per turn on writes — half
  extraction, half conflict detection — and the read path makes **none**. That is a consequence of decisions argued on correctness
  grounds — arbitration refuses a model for explainability, ranking is
  arithmetic for determinism — not an optimisation.
- **Similarity cannot carry any write-path decision.** It cannot generate
  conflict candidates (a contradiction scores 0.285, below unrelated noise at
  0.478), identify corroboration, or retrieve a procedure. Every stage that
  works is keyed on structure, and `SLOT` is imported by nine modules
  outside the one that defines it.
- **Most of the valuable results are null results.** Reflection makes the
  budgeted answer worse; three of I8's four mechanisms move nothing; the entity
  graph has one node; per-type scheduling barely helps. A measurement saying
  *this did nothing* is what saves the next person a month.

## Findings that reversed an obvious approach

Worth reading before extending any of these.

- **Salience must not be added to a relevance score.** It moves the correct
  answer *down*. Importance and relevance are different axes.
- **Decay rate must be scaled by memory type.** One half-life drops fourteen
  standing beliefs. What decays is relevance, not truth.
- **`invalid_at` was answering two questions**, retiring a claim nine months
  before it was recorded. `valid_to` is when a fact stopped being true;
  `invalid_at` is when the store found out.
- **The read path assumed *now* in three places.** Routing a dated question
  fixes nothing until `live_only` *and* the I5 tier cap are released: 0 → 0 →
  1 → 4 of 4.
- **A relative-time parser must be able to decline.** `diff against last week`
  is a step inside a taught procedure; resolving it dates the recipe.
- **Deferred consolidation costs the window, not the compute.** 13× cheaper,
  identical store, 11 of 24 turns wrong. The gate that closes it is `slot_of`,
  already computed by the write path.
- **`store.replace(consolidate(store.all()))` destroys 33 memories** when a
  turn lands mid-job. A write-back must record *which ids* it read: absence
  means both "merged away" and "never seen".
- **Competence needs three verdicts, not two.** An unnameable claim is outside
  the *vocabulary*, not the writer's domain; discounting it punishes a reliable
  agent for a gap in your slot table.
- **`FIRST_PARTY` is a threshold, so 0.9 and 1.0 are the same number.** An
  agent above the line overwrites the user's own belief by being newer.
- **`leak_check` cannot catch a leak** — only a bug in the filter that prevents
  leaks. Always zero, and valuable entirely for the day it is not.
- **An invariant computed over the data it checks cannot catch an outlier**
  that moves the reference. Leave-one-out.
- **Component metrics are wrong first.** The first version scored a working
  system at 0.733, 0.600 and 0.500; every number was the metric.

## Discipline that produced all of it

Land code, **run it**, then write prose quoting measured output. Every number
guessed in this project has been wrong — including *"twenty months"* that
measured 249 days, an audit denominator that reported a 100% failure as 92%,
and *"four tokens of headroom"* where the delta is five.

- Commit per lesson. **Cold-read each module in syllabus order, reading the
  Mechanism and Design-decisions sections in full, before its last commit.** An
  opener scan is not a cold read; every seam found in Level 3 was in a middle.
- `validate_expected_output.py` runs all 84 labs and checks every quoted figure
  against what the lab printed. It has caught a claim in nearly every module.
- Anything reachable from the CLI must be **selectable** from it — `--profile
  advanced` was in `PROFILES` and rejected by argparse for two modules.

## What v0.3 still gets wrong

Six open items, each measured and each naming the lesson that found it. Run
`curriculum/advanced/capstone-finale/lab/lab.py` for the current list; two of
them are the same stage — extraction — seen from different lessons, which is
visible only in the collected report.
