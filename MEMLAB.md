# The `memlab` API

Every lab imports from `memlab`, the package you spend the course building.
This page is the reference that was missing: **where each thing lives, and what
it takes.**

It is not the whole package. The 168 lab files import 124 distinct `memlab`
names between them; the 23 below account for **74% of all import occurrences**,
which is why they are the ones written down. For anything else, the lab's own
`solution.py` sits next to its stub and shows the import it used.

Signatures here are read from the code, not typed from memory — if one looks
wrong, the code wins, and it is a bug worth reporting.

---

## The record

Everything the write path produces is a `Memory`.

```python
from memlab.types import Memory, MemoryType, Provenance, Scope, Tier
```

`Memory` is a frozen dataclass with seventeen fields. The ones you touch early:

| field | what it holds |
|---|---|
| `content` | the claim, as text |
| `type` | `MemoryType` — `episodic`, `semantic`, `procedural`, `working` |
| `scope` | who it belongs to |
| `provenance` | where it came from |
| `happened_at` / `recorded_at` | when it was true / when we wrote it down |
| `valid_from` / `valid_to` | when the fact was true in the world |
| `invalid_at` | when *the store found out* — a different question |
| `superseded_by` | the id of the belief that replaced it |
| `confidence`, `salience`, `tier`, `access_count` | ranking and lifecycle |
| `entities`, `derived_from`, `id` | resolution, corroboration, identity |

```python
Scope(user: str, agent: str | None = None, session: str | None = None)
Provenance(source_id: str, speaker: str, authority: float = 1.0)
```

`Scope` is "the key every read must filter on before it ranks anything".
`Tier` is `scratch | working | long_term`.

Retiring a belief is a method, never a delete:

```python
memory.supersede(by: str, at: datetime, found_out: datetime | None = None, event_end: bool = False) -> Memory
```

## The store

```python
from memlab.store.jsonl import JsonlStore

store = JsonlStore(path)        # str | Path
store.add(memories) -> int      # append; content-addressed ids make re-ingest idempotent
store.all() -> list[Memory]
store.live() -> list[Memory]    # not superseded, not expired
store.replace(memories) -> int  # rewrite the log wholesale
store.clear() -> None
```

`memlab.store.sqlite.SqliteStore` has the same shape and arrives later.

## Which system you are running

The capstone grows across the course, so a lab has to say *which* version of it
to use. That is what a profile or a snapshot is.

```python
from memlab.pipeline import at, get

get("beginner")        # Level 1 as shipped; also "intermediate", "advanced"
at("I3")               # the system exactly as module I3 left it
```

Snapshots exist so a number measured once stays true. `I1`–`I8` are the
intermediate modules, `A1`–`A9` the advanced ones. If you change shared code and
a later lesson's figure moves, that is the snapshot doing its job.

## Running the write path

```python
from memlab.app.chat import ask, ingest

ingest(store, scope, pipeline=None, before_session=14) -> int   # memories actually written
ask(store, scope, question, k=5, pipeline=None, budget=400) -> tuple[str, list[Hit]]
```

`before_session=14` is the default because **session 14 is held out** — it is
the question, not a memory.

## The read path

```python
from memlab.retrieve.embedding import EmbeddingRetriever, Hit

EmbeddingRetriever().search(query, memories, scope, k=5, live_only=True) -> list[Hit]
```

A `Hit` is `(memory, score, query)`. Then pack it into a context window:

```python
from memlab.assemble.simple import assemble, estimate_tokens

assemble(hits, budget_tokens=400) -> str   # highest first, stop at budget, never split
estimate_tokens(text) -> int               # crude on purpose
```

## The model

Labs run offline against a deterministic fake. That is what makes "your numbers
should be identical to the ones on the page" a real promise.

```python
from memlab.llm.fake import cosine, embed_text

embed_text(text) -> list[float]   # deterministic, L2-normalised, dependency-free
cosine(a, b) -> float
```

It is a *lexical* model, and that limit is teaching material rather than a
shortcoming to work around.

## The corpus and the answer key

```python
from memlab.fixtures import load_gold, load_turns

load_turns(user_only=False) -> list[dict]   # Priya's 14 sessions, in order
load_gold() -> dict                          # ground truth, and the index lessons cite
```

A turn is a dict with `session`, `role`, `text`, `ts`.

## The exam

```python
from memlab.eval.exam import QUESTION, exam_answer

QUESTION      # "where do I work and what should I not eat?"
exam_answer(memories, scope) -> ExamAnswer
```

## Belief updating

```python
from memlab.evolve.conflict import SLOTS, detect, slot_of

slot_of(memory) -> str | None    # which attribute this claim fills
detect(memories, scope, client=None) -> list[Conflict]
SLOTS                            # the attribute table: employer, diet, ...
```

`slot_of` is the quiet workhorse of the course — structure, not similarity, is
what generates conflict candidates. Similarity cannot: a genuine contradiction
in this corpus scores 0.285, below unrelated noise at 0.478.

---

## Finding anything else

```bash
uv run python tools/show.py <lesson-id>          # what a solved lab prints
uv run python tools/show.py --check <lesson-id>  # whether YOUR lab is right
grep -rn "from memlab" curriculum/*/*/lab/solution.py | grep <name>
```

The package source is under `capstone/src/memlab/`.
