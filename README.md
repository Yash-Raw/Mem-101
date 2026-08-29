# Building a Memory Layer

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
uv sync --dev
uv run python tools/show.py memory-is-not-rag
```

That prints the table above for real, from the corpus, on your machine. Then
read [SYLLABUS.md](SYLLABUS.md) for the full map.

(`show.py` runs a lab with its reference solution filled in. The lab file
itself, `lab/lab.py`, is a stub that raises `NotImplementedError` until *you*
fill it in — that is the exercise, and the section below is how it works.)

**No API key is needed.** Labs run against a deterministic local model whose
embeddings are genuinely responsive to wording, so retrieval lessons teach real
behaviour offline and in CI. Set `MEMLAB_LLM=anthropic` if you want live calls.

## How to take this course

**You need** Python 3.11+ and [uv](https://docs.astral.sh/uv/). The system
`python3` on many machines is 3.9, so every command here is `uv run` — that is
not a style choice, it is what makes the version right. You never need an API
key, at any level.

**The loop, for each of the 84 lessons:**

1. **Read the lesson** — `curriculum/<level>/<lesson>/index.md`. Every one ends
   with a `Why this isn't RAG` section; if you read nothing else, read those.
2. **Open its lab** — `lab/lab.py`. Exactly one function is stubbed with
   `raise NotImplementedError` and a `TODO` describing what it must return.
3. **Fill the stub, then run the file:**
   ```bash
   uv run python curriculum/beginner/memory-is-not-rag/lab/lab.py
   ```
   It prints a table. **The lesson quotes that same table.** Matching it is how
   you know you are right — the fake model is deterministic, so your numbers
   should be identical to the ones on the page, not merely similar.
   Stuck, or want to see the target first?
   `uv run python tools/show.py <lesson-id>` prints what the lab produces when
   it is solved — the same code path CI uses to check the lesson's prose.
4. **Then read `solution.py`**, which sits next to the stub on purpose. This is
   not a test you can cheat; it is a course you can get stuck in. Read it when
   comparing beats grinding.

**About `pytest`.** Each lab ships a `test_lab.py`, but it is not a grader — it
pins the *lesson's claims* against the reference solution, so a lesson's numbers
cannot silently rot. One consequence surprises people: every lab's first test is
`test_stub_is_runnable`, which asserts the stub still raises `NotImplementedError`.
**Implement the stub correctly and that test goes red.** That is the exercise
working, not you breaking it. Run the suite to check the repo is healthy:

```bash
uv run pytest -q                                              # all 823
uv run pytest curriculum/beginner/memory-is-not-rag/lab/ -q   # one lesson
```

**Three ways in:**

- **Thirty minutes** — run the lab above and read `memory-is-not-rag`. That is
  the whole argument, demonstrated rather than asserted.
- **Front to back** — [SYLLABUS.md](SYLLABUS.md) is the order, and it is proven
  to be a valid topological sort of the prerequisite graph, so nothing ever
  depends on something you have not met.
- **Straight at your bug** — scan the syllabus for the failure you are actually
  hitting. Roughly half the course is `evolve` and `govern`; only about 11% is
  retrieval.

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
| `docs/` | The site: its stylesheet, the two interactive pages' scripts, and symlinks to everything above. |

One conversation — Priya, 14 sessions, March 2025 to August 2026 — runs through
every lab at every level. By the time you are fixing belief updating in
Intermediate, you are fixing a contradiction you created yourself in Beginner.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). `uv run python tools/check.py` before every commit.

## Licence

Two licences, split by what the file is.

| Path | Licence | |
|---|---|---|
| `curriculum/`, `concepts/`, `landscape/`, `SYLLABUS.md`, `README.md`, `CONTRIBUTING.md`, `map.md`, `atlas.md` | **CC BY 4.0** | [LICENSE-CONTENT](LICENSE-CONTENT) |
| `capstone/`, `tools/`, `docs/assets/`, `overrides/`, and every `lab/*.py` | **MIT** | [LICENSE](LICENSE) |

Teach from it, translate it, adapt it, use it inside a paid course — all fine,
with credit. Lift `memlab` into your own system — fine, no credit required.
