# Building a Memory Layer

> The write path is the part the tutorials skip.

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
uv run python curriculum/beginner/memory-is-not-rag/lab/lab.py
```

Then read [SYLLABUS.md](SYLLABUS.md) for the full map.

**No API key is needed.** Labs run against a deterministic local model whose
embeddings are genuinely responsive to wording, so retrieval lessons teach real
behaviour offline and in CI. Set `MEMLAB_LLM=anthropic` if you want live calls.

## How it is organised

| Path | What it holds |
|---|---|
| `curriculum/` | The lessons, in three levels. `syllabus.yml` is the single source of truth for order. |
| `concepts/` | One page per idea, linked from everywhere it appears. |
| `capstone/` | `memlab`, the system you build — plus the canonical corpus every lab uses. |
| `landscape/` | Named tools and benchmarks, quarantined and dated, so the lessons never rot. |
| `tools/` | Validators that keep all of the above honest. |

One conversation — Priya, 14 sessions, March 2025 to August 2026 — runs through
every lab at every level. By the time you are fixing belief updating in
Intermediate, you are fixing a contradiction you created yourself in Beginner.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). `uv run python tools/check.py` before every commit.
