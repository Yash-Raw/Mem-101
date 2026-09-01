# Building a Memory Layer

[![CI](https://github.com/Yash-Raw/Mem-101/actions/workflows/ci.yml/badge.svg)](https://github.com/Yash-Raw/Mem-101/actions/workflows/ci.yml)
[![Site](https://img.shields.io/badge/site-yash--raw.github.io%2FMem--101-1f6feb)](https://yash-raw.github.io/Mem-101/)
[![Licence](https://img.shields.io/badge/licence-CC%20BY%204.0%20prose%20%C2%B7%20MIT%20code-blue)](#licence)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776ab)](https://docs.astral.sh/uv/)

> The write path is the part the tutorials skip.

**Read it online: <https://yash-raw.github.io/Mem-101/>**

Two ways to see the shape of it before you start: the
[course map](https://yash-raw.github.io/Mem-101/map/) is all 84 lessons by
level and pipeline stage, filterable; the
[concept atlas](https://yash-raw.github.io/Mem-101/atlas/) is the concept web
underneath the reading order — which lesson teaches an idea, and which later ones
lean on it. Both are generated from `syllabus.yml` and the
prerequisite graph, so neither can drift from the course.

Search for how to build an agent memory layer and you mostly find RAG tutorials
wearing a different hat: chunk, embed, retrieve, done. That answers a different
question. Retrieval is a **read path over a corpus someone else wrote**. A
memory layer is dominated by the **write path** — what gets extracted from an
interaction, how facts are reconciled when they conflict, what decays, what gets
promoted from an episode to a belief, and how recall is scoped to one person at
one moment in time.

This is the resource that should have existed: 84 lessons across three levels,
every one with a runnable Python lab, building toward a single memory system you
grow from naive to production.

## The argument, in one table

Priya has talked to an assistant for 17 months. She asks: *"where do I work and
what should I not eat?"* Every fact needed is in her history. A correctly-built
retrieval pipeline ranks her **former** employer 1st of 24 and her **current**
employer 18th.

That is lesson 00, and you run it yourself in the first thirty minutes.

## Start here

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # if you do not have uv
uv sync --dev
```

Then open [Memory Is Not RAG](curriculum/beginner/memory-is-not-rag/index.md)
and work its lab. It is the first of four lessons in *Why Memory Is Not RAG*,
about two hours in total.

If you get stuck, `uv run python tools/show.py memory-is-not-rag` prints what
that lab produces once it is solved. It is a way out of a hole, not a first
step — running it before you attempt the lab gives away the answer.

**No API key is needed.** Labs run against a deterministic local model whose
embeddings are genuinely responsive to wording, so retrieval lessons teach real
behaviour offline and in CI. Set `MEMLAB_LLM=anthropic` if you want live calls.

## How to take this course

**You need** Python 3.11+ and [uv](https://docs.astral.sh/uv/). The system
`python3` on many machines is 3.9, so every command here is `uv run` — that is
not a style choice, it is what makes the version right. You never need an API
key, at any level.

**The loop, for each of the 84 lessons:**

1. **Read the lesson** — `curriculum/<level>/<lesson>/index.md`. Every one has a
   `Why this isn't RAG` section, third of ten; if you read nothing else, read those.
2. **Open its lab** — `lab/lab.py`. Exactly one function is stubbed with
   `raise NotImplementedError` and a `TODO` describing what it must return.
   Everything the TODO names is imported at the top of the stub;
   [the memlab API](MEMLAB.md) is the reference for the rest of the package.
3. **Fill the stub, then run the file:**
   ```bash
   uv run python curriculum/beginner/memory-is-not-rag/lab/lab.py
   ```
   It prints a table. **The lesson quotes that same table.** The fake model is
   deterministic, so your numbers should be identical to the ones on the page,
   not merely similar — and you do not have to compare them by eye:
   ```bash
   uv run python tools/show.py --check memory-is-not-rag
   ```
   That runs *your* `lab.py` with nothing patched over it and diffs the output
   against the reference. It is the one command that tells you that you got it
   right. Stuck, or want to see the target first? Drop the `--check` and
   `tools/show.py <lesson-id>` prints what the lab produces when it is solved —
   the same code path CI uses to check the lesson's prose.
4. **Then read `solution.py`**, which sits next to the stub on purpose. This is
   not a test you can cheat; it is a course you can get stuck in. Read it when
   comparing beats grinding.

**About `pytest`.** Each lab ships a `test_lab.py`, but it is not a grader — it
pins the *lesson's claims* against the reference solution, so a lesson's numbers
cannot silently rot. One consequence surprises people: every lab's first test is
`test_stub_is_runnable`, which asserts the stub still raises `NotImplementedError`.
**Implement the stub correctly and that test goes red.** That is the exercise
working, not you breaking it — `show.py --check` is where you get told you are
right, and `pytest` is how you check the *repository* is healthy:

```bash
uv run pytest -q                                              # all 823
uv run pytest curriculum/beginner/memory-is-not-rag/lab/ -q   # one lesson
```

**If you are not starting from the beginning.** [SYLLABUS.md](SYLLABUS.md) is
the order, proven to be a valid topological sort of the prerequisite graph, so
nothing ever depends on something you have not met. Or scan the
[course map](https://yash-raw.github.io/Mem-101/map/) for the failure you are
actually hitting — roughly half the course is `evolve` and `govern`, and only
about 11% is retrieval.

**If a number moves under you.** Lessons quote measured output, and shared code
changes as the capstone grows — so each lesson pins itself to a *module
snapshot* (`pipeline.at("I3")` is "the system as module I3 left it"). If you
edit `memlab` and a later lesson's figure shifts, that is the snapshot doing its
job. `uv run python tools/dump_snapshots.py` shows what moved.


## How it is organised

| Path | What it holds |
|---|---|
| `curriculum/` | The lessons, in three levels. `syllabus.yml` is the single source of truth for order. |
| `concepts/` | One page per idea, linked from everywhere it appears. |
| `capstone/` | `memlab`, the system you build — plus the canonical corpus every lab uses. |
| `landscape/` | Named tools and benchmarks, quarantined and dated, so the lessons never rot. |
| `tools/` | Validators that keep all of the above honest. |
| `docs/` | The site: its stylesheet, the interactive pages' scripts, and symlinks to everything above. |
| `modules/` | One generated overview per module — the unit between a lesson and a level. |
| `timeline.md` | Priya's fourteen sessions, annotated from `gold.yml` with the lesson each moment belongs to. |
| `MEMLAB.md` | The `memlab` API a lab actually uses — where each thing lives, and what it takes. |

One conversation — Priya, 14 sessions, March 2025 to August 2026 — runs through
every lab at every level. By the time you are fixing belief updating in
Intermediate, you are fixing a contradiction you created yourself in Beginner.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). `uv run python tools/check.py` before every commit.

## Licence

Two licences, split by what the file is.

| Path | Licence | |
|---|---|---|
| `curriculum/`, `concepts/`, `landscape/`, `modules/`, `SYLLABUS.md`, `README.md`, `CONTRIBUTING.md`, `MEMLAB.md`, `map.md`, `atlas.md` | **CC BY 4.0** | [LICENSE-CONTENT](LICENSE-CONTENT) |
| `capstone/`, `tools/`, `docs/assets/`, `overrides/`, and every `lab/*.py` | **MIT** | [LICENSE](LICENSE) |

Teach from it, translate it, adapt it, use it inside a paid course — all fine,
with credit. Lift `memlab` into your own system — fine, no credit required.
