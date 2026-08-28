# Contributing

Run `uv run python tools/check.py` and `uv run pytest -q` before every commit.
CI runs both, plus `ruff`.

## Conventions

These are enforced by validators, not by review. Each has a reason.

**C1 — Directory names are stable, number-free slugs.** `conflict-resolution/`,
never `03-conflict-resolution/`. Numeric prefixes turn every reorder into a
URL-breaking rename. Ordering is data, and it lives in `curriculum/syllabus.yml`.

**C2 — Linear order lives in exactly one file.** `syllabus.yml` holds it;
`SYLLABUS.md` is generated. Never hand-edit generated output.

**C3 — The prerequisite *graph* lives in lesson frontmatter, not in syllabus.yml.**
These are two different objects: the syllabus is one valid *linearization* of the
DAG. `validate_graph.py` proves they agree.

**C4 — `id` equals the directory name (lessons) or the filename (concepts).**
Renaming is a breaking change; add a redirect.

**C5 — Cross-links are relative and end in `.md`.** This is the only form that
renders correctly both when browsing the repo on GitHub and in the built site.
Absolute links fail validation.

**C6 — Diagrams are fenced ` ```mermaid ` blocks**, not image files. Diffable,
reviewable, no asset pipeline.

**C7 — Labs are `.py`, never notebooks.** Each lesson with a lab ships
`lab.py` (stub), `solution.py` (reference), and `test_lab.py`.

**C8 — Generated regions** sit between `<!-- graph:begin -->` and
`<!-- graph:end -->`. Never edit inside them; run `tools/build_graph.py`.

**C9 — Named tools, vendors, and benchmark numbers appear only in `landscape/`,**
or inside a `<!-- landscape:begin -->…<!-- landscape:end -->` block in a lesson.
The conceptual spine must survive any product being renamed or abandoned. Add
new names to `landscape/registry.yml` as soon as they appear in a draft.

## Writing a lesson

Lessons carry ten `##` sections in a fixed order — see `LESSON_SECTIONS` in
`tools/validate_frontmatter.py`. Two are load-bearing:

- **`Why this isn't RAG`** is mandatory. If it feels redundant, reconsider the
  lesson. (`rag_contrast: n/a` in frontmatter exempts a lesson, and needs a reason.)
- **`Failure modes`** needs at least two table rows. A mechanism without its
  failure modes is marketing.

**Use the canonical corpus.** `capstone/fixtures/corpus.jsonl` is seeded with a
job change, entity aliases, a diet chain, a genuine contradiction, relative time
references, PII plus a deletion request, a taught procedure, and low-authority
hearsay. `gold.yml` maps each seeded phenomenon to the lesson that confronts it.
Cite it rather than inventing an example — the continuity across 84 lessons is
the whole design.

**Assert exact output.** The fake backend is deterministic, so labs can assert
precise rankings and scores. When a lesson quotes a number, a test should pin it.

## Writing a lab

Labs must run offline with no API key. Embeddings come from
`memlab.llm.fake.embed_text`. Completions are fixture-backed — author them with
`register_fixture(messages, response, schema)`, which computes the key and writes
JSON without calling a model, so fixtures stay reviewable in a diff.

## Lab tests

Load the lab's own modules through `memlab.labkit`, never by bare name:

```python
from memlab import labkit

_solution = labkit.solution(__file__)
_lab = labkit.lab(__file__)
```

Eighty-four labs means eighty-four modules called `solution`. A bare
`from solution import ...` resolves to whichever one Python cached first, so the
second lab in a run silently tests the first lab's code. `labkit` namespaces by
lesson; `validate_structure.py` enforces it.

Every lab test starts with `test_stub_is_runnable`, asserting the stub raises
`NotImplementedError` — proof the exercise is actually left undone.

## Landscape pages

Every page needs `last_verified`, `category`, and `volatility`. High-volatility
pages **fail CI at 180 days**. Re-verify or delete; do not extend the date
without re-checking. Mark vendor-reported figures with
`claims_are_vendor_sourced: true`.

## Licensing of contributions

Contributions are offered under the same split as the repository: CC BY 4.0 for
prose, MIT for code. See [LICENSE](LICENSE) and [LICENSE-CONTENT](LICENSE-CONTENT).
