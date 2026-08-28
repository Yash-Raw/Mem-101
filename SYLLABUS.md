# Building a Memory Layer

> The write path is the part the tutorials skip.

84 lessons across 21 modules and 3 levels. Every lesson carries a lifecycle `stage`, a prerequisite list, a runnable lab, and a piece of the capstone.

<!-- generated:begin --> <!-- Do not edit: `uv run python tools/render_syllabus.py` -->

## Where the mass sits

A RAG tutorial spends ~85% of its length on `retrieve`. This course does not, and the table below is the argument:

| Stage | | Lessons | Share |
|---|---|--:|--:|
| `orientation` | framing the problem | 4 | ██ 5% |
| `extract` | turns into facts | 6 | ███ 7% |
| `store` | where facts live | 17 | ████████ 20% |
| `retrieve` | getting them back | 9 | ████ 11% |
| `evolve` | keeping them true | 20 | ██████████ 24% |
| `assemble` | fitting the budget | 7 | ███ 8% |
| `govern` | privacy, eval, ops | 21 | ██████████ 25% |

## The three levels

### The Loop · *How does a system remember at all?*

A CLI assistant that survives process restart, builds its own corpus from conversation, and is visibly broken in seven documented ways.

13 lessons · 4 modules

### The Write Path in Earnest · *How does memory stay correct as it grows?*

memlab v0.2: typed memories, entity resolution, deterministic belief updating, salience-driven decay, and budgeted context assembly.

31 lessons · 8 modules

### Time, Scale, Multiplicity, Trust · *How does it survive time, scale, multiplicity, and scrutiny?*

memlab v0.3: bi-temporal, multi-agent, governed, benchmarked, with cascade deletion that provably reaches derived data.

40 lessons · 9 modules

## Contents

### The Loop

**Why Memory Is Not RAG**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 1 | [Memory Is Not RAG](curriculum/beginner/memory-is-not-rag/index.md) | `orientation` | Separate the read path over a given corpus from the write path that authors its own. |
| 2 | [The Taxonomy That Actually Routes](curriculum/beginner/memory-taxonomy/index.md) | `orientation` | Treat working/episodic/semantic/procedural as engineering categories with distinct lifecycles. |
| 3 | [Context Is Not Memory](curriculum/beginner/context-is-not-memory/index.md) | `orientation` | Explain why a larger context window is not a memory layer: no selection, persistence, or mutation. |
| 4 | [Anatomy of a Memory Layer](curriculum/beginner/anatomy-of-a-memory-layer/index.md) | `orientation` | Name every component the rest of the course builds. The reference diagram. |

**The Write Path, Naively**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 5 | [Designing the Memory Record](curriculum/beginner/the-memory-record/index.md) | `store` | Choose the fields now that Intermediate will depend on: scope, provenance, event time, confidence. |
| 6 | [Naive Extraction](curriculum/beginner/naive-extraction/index.md) | `extract` | Pull durable facts from a turn with structured output, and cause your first over-extraction disaster. |
| 7 | [Writing Memories Down](curriculum/beginner/writing-memories-down/index.md) | `store` | Append-only JSONL with stable ids and idempotent writes; meet the duplicate problem it creates. |

**The Read Path, Honestly**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 8 | [Embedding Recall](curriculum/beginner/embedding-recall/index.md) | `retrieve` | Build minimum-viable vector search, framed as one strategy among several. |
| 9 | [Retrieval Is Not Enough](curriculum/beginner/retrieval-is-not-enough/index.md) | `retrieve` | Scope by owner before ranking; meet semantically-close-but-wrong and confidently-stale. |
| 10 | [Getting Memories Into the Prompt](curriculum/beginner/context-assembly-v0/index.md) | `assemble` | Inject recalled beliefs with attribution, and mark them as beliefs rather than ground truth. |

**The Loop Closes**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 11 | [Session Memory vs Long-Term Memory](curriculum/beginner/session-vs-longterm/index.md) | `evolve` | Decide what dies at end of session and what gets promoted. |
| 12 | [Your First Memory Layer](curriculum/beginner/your-first-memory-layer/index.md) | `assemble` | Ship memlab v0.1: an assistant that survives restart. |
| 13 | [Watching It Fail](curriculum/beginner/watching-it-fail/index.md) | `govern` | Catalogue the seven failures you now have; each one names the Intermediate module that fixes it. |

### The Write Path in Earnest

**Typed Memory & Extraction Pipelines**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 14 | [The Typed Memory Model](curriculum/intermediate/typed-memory-model/index.md) | `store` | Give each memory type its own schema, lifecycle, and update rule. |
| 15 | [Extraction Pipelines](curriculum/intermediate/extraction-pipelines/index.md) | `extract` | Stage candidate generation, salience filtering, schema validation, and type routing. |
| 16 | [Precision and Recall on the Write Path](curriculum/intermediate/extraction-quality/index.md) | `extract` | Measure extraction quality and price the compounding cost of over-extraction. |
| 17 | [Atomic Memories](curriculum/intermediate/atomic-memories/index.md) | `extract` | Size a memory so it can be updated later; recognise one that is too big to revise. |

**Identity & Entity Resolution**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 18 | [Entities and Aliases](curriculum/intermediate/entities-and-aliases/index.md) | `store` | Collapse 'my wife', 'Sarah', and 'S.' into one canonical node. |
| 19 | [Entity Resolution](curriculum/intermediate/entity-resolution/index.md) | `store` | Block, score, merge, and un-merge; handle the split problem. |
| 20 | [Scopes and Namespaces](curriculum/intermediate/scopes-and-namespaces/index.md) | `store` | Key memory by user, agent, org, and session — the multi-tenancy substrate. |

**Consolidation**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 21 | [Deduplication](curriculum/intermediate/deduplication/index.md) | `evolve` | Detect exact, near, and semantic duplicates; choose write-time vs read-time dedupe. |
| 22 | [Summarization and Compaction](curriculum/intermediate/summarization-and-compaction/index.md) | `evolve` | Build rolling summaries and hierarchical digests without losing the originals. |
| 23 | [Semantic Drift](curriculum/intermediate/semantic-drift/index.md) | `evolve` | Bound degradation by re-deriving from anchored originals, never summarizing summaries. |
| 24 | [From Episode to Belief](curriculum/intermediate/episodic-to-semantic/index.md) | `evolve` | Promote 'on Tuesday she said X' to 'she prefers X' — and know when that is wrong. |

**Conflict Resolution & Belief Updating**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 25 | [Contradiction Detection](curriculum/intermediate/contradiction-detection/index.md) | `evolve` | Separate a genuine contradiction from a legitimate change over time. |
| 26 | [ADD, UPDATE, DELETE, NOOP](curriculum/intermediate/memory-operations/index.md) | `evolve` | See why a free-form LLM UPDATE decision is the largest source of silent memory corruption. |
| 27 | [Deterministic Arbitration](curriculum/intermediate/deterministic-freshness/index.md) | `evolve` | Confine the model to detection and let rules decide, using recency, authority, and explicitness. |
| 28 | [Supersede, Never Destroy](curriculum/intermediate/supersession-not-deletion/index.md) | `evolve` | Keep the audit trail that makes bi-temporal modeling possible later. |

**Forgetting**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 29 | [Why Forgetting Is a Feature](curriculum/intermediate/why-forgetting-is-a-feature/index.md) | `evolve` | Justify forgetting on cost, latency, precision, privacy, and coherence. |
| 30 | [Salience Scoring](curriculum/intermediate/salience-scoring/index.md) | `evolve` | Combine recency, reinforcement, explicit markers, and retrieval-hit feedback. |
| 31 | [Decay and Memory Tiers](curriculum/intermediate/decay-and-tiers/index.md) | `evolve` | Move memories across scratchpad, working, and long-term tiers under decay and reinforcement. |
| 32 | [Forgetting Under a Budget](curriculum/intermediate/budgeted-forgetting/index.md) | `evolve` | Evict, archive, or quarantine within a bounded store, and tune without losing the user. |

**Retrieval Done Properly**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 33 | [Scope, Then Rank](curriculum/intermediate/scope-then-rank/index.md) | `retrieve` | Apply hard filters on owner, type, and validity before any similarity is computed. |
| 34 | [Hybrid Ranking](curriculum/intermediate/hybrid-ranking/index.md) | `retrieve` | Fuse semantic, lexical, recency, and salience signals; add diversity. |
| 35 | [The Query Is Not the Last Message](curriculum/intermediate/query-formulation/index.md) | `retrieve` | Rewrite and expand queries; condition retrieval on intent. |
| 36 | [Should I Even Look?](curriculum/intermediate/retrieval-triggers/index.md) | `retrieve` | Choose between always-on retrieval and memory as a tool call. |

**Stores**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 37 | [Vector Stores for Data That Changes](curriculum/intermediate/vector-stores-for-mutable-data/index.md) | `store` | Handle reindexing, tombstones, and embedding staleness after an UPDATE. |
| 38 | [The Underrated Default](curriculum/intermediate/relational-stores/index.md) | `store` | Use SQLite with FTS as a genuinely good memory store. |
| 39 | [Graph Stores](curriculum/intermediate/graph-stores/index.md) | `store` | Model entities and relations; traverse for multi-hop recall. |
| 40 | [Hybrid Architecture](curriculum/intermediate/hybrid-architecture/index.md) | `store` | Pick a store per memory type and keep them consistent under write fan-out. |

**Context Assembly Under Budget**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 41 | [The Packing Problem](curriculum/intermediate/the-packing-problem/index.md) | `assemble` | Treat the token budget as constrained selection, not truncation. |
| 42 | [Ordering and Formatting](curriculum/intermediate/ordering-and-formatting/index.md) | `assemble` | Price the line format, and check whether ordering by score costs anything. |
| 43 | [What Must Never Be Dropped](curriculum/intermediate/compaction-safety/index.md) | `assemble` | Make coverage an invariant of the packer, derived from the question rather than a topic list. |
| 44 | [Does This Earn Its Tokens?](curriculum/intermediate/slot-value/index.md) | `assemble` | Price every element of the context, including the ones that are not memories. |

### Time, Scale, Multiplicity, Trust

**Temporal Reasoning & Bi-Temporal Modeling**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 45 | [Two Clocks](curriculum/advanced/two-clocks/index.md) | `store` | Audit which of the two clocks is actually running; four instants, not two. |
| 46 | [Validity Intervals](curriculum/advanced/validity-intervals/index.md) | `store` | Separate when a fact was true from when it was believed, and query both. |
| 47 | [Three Temporal Questions](curriculum/advanced/temporal-questions/index.md) | `retrieve` | Route the three temporal questions, and release every filter that assumed now. |
| 48 | [Resolving 'Last Week'](curriculum/advanced/relative-time-resolution/index.md) | `extract` | Four classes of relative reference, and the one you must not resolve. |
| 49 | [Temporal Knowledge Graphs](curriculum/advanced/temporal-knowledge-graphs/index.md) | `store` | Cascade invalidation through the derivation graph -- the one that actually has edges. |

**Offline Consolidation**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 50 | [Sleep-Time Compute](curriculum/advanced/sleep-time-compute/index.md) | `evolve` | The window is the cost, not the compute -- and the gate that closes it is already computed. |
| 51 | [Background Job Mechanics](curriculum/advanced/background-job-mechanics/index.md) | `evolve` | Write back only what the job read -- absence means two opposite things. |
| 52 | [Reflection and Insight](curriculum/advanced/reflection-and-insight/index.md) | `evolve` | Derive higher-order beliefs, and measure that storing them makes the answer worse. |
| 53 | [Promotion as a Release](curriculum/advanced/promotion-as-release/index.md) | `evolve` | Measure a consolidation before applying it, and be able to take it back. |

**Multi-Agent & Shared Memory**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 54 | [Memory Topologies](curriculum/advanced/memory-topologies/index.md) | `store` | Price each shape by what a reader loses -- and by what it leaks. |
| 55 | [Provenance and Trust](curriculum/advanced/provenance-and-trust/index.md) | `govern` | Trust the claim, not the claimant -- and flag what cannot be assessed. |
| 56 | [Cross-Agent Write Conflicts](curriculum/advanced/cross-agent-write-conflicts/index.md) | `evolve` | The precedence rule is a threshold -- and above it, recency decides. |
| 57 | [Memory Access Control](curriculum/advanced/memory-access-control/index.md) | `govern` | Say no to a write, and assert the filter that says no to a read. |

**Personalization & User Modeling**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 58 | [From Facts to a User Model](curriculum/advanced/from-facts-to-a-user-model/index.md) | `evolve` | Key the model on attributes, and keep what does not fit. |
| 59 | [Behaviour as Memory](curriculum/advanced/implicit-signals/index.md) | `extract` | A correction is a labelled negative example, and it always arrives late. |
| 60 | [Personalization Without Creepiness](curriculum/advanced/applying-the-model/index.md) | `assemble` | Split the model by how each attribute is used, and report what was withheld. |
| 61 | [Cold Start and Shared Accounts](curriculum/advanced/cold-start-and-shared-accounts/index.md) | `retrieve` | Handle sparsity, multi-persona accounts, and household devices. |

**Procedural Memory & Learning From Experience**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 62 | [Procedural Memory](curriculum/advanced/procedural-memory/index.md) | `store` | Treat skills, workflows, and tool-use traces as first-class memory. |
| 63 | [Learning From Outcomes](curriculum/advanced/learning-from-outcomes/index.md) | `evolve` | Store corrections and failures as a lessons-learned store. |
| 64 | [Retrieving Procedures](curriculum/advanced/retrieving-procedures/index.md) | `retrieve` | Use a different index, trigger, and injection point than facts. |

**Privacy, PII, Deletion & Right to Be Forgotten**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 65 | [PII on the Write Path](curriculum/advanced/pii-on-the-write-path/index.md) | `govern` | Detect, classify, and gate memory-worthiness before anything is stored. |
| 66 | [Redaction and Minimization](curriculum/advanced/redaction-and-minimization/index.md) | `govern` | Store less on purpose; encrypt at the field level. |
| 67 | [Deletion That Actually Deletes](curriculum/advanced/deletion-that-actually-deletes/index.md) | `govern` | Cascade a delete through summaries, embeddings, graph edges, and caches. |
| 68 | [Proving You Forgot](curriculum/advanced/rtbf-and-auditability/index.md) | `govern` | Demonstrate deletion, retention policy, and regional constraints. |
| 69 | [Memory Attacks](curriculum/advanced/memory-attacks/index.md) | `govern` | Defend against poisoning, injection, cross-user leakage, and extraction. |

**Evaluating Memory Systems**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 70 | [Why Memory Eval Is Hard](curriculum/advanced/why-memory-eval-is-hard/index.md) | `govern` | Confront the absent corpus, moving ground truth, and unlabelled write path. |
| 71 | [Component Metrics](curriculum/advanced/component-metrics/index.md) | `govern` | Measure extraction P/R, dedupe correctness, arbitration accuracy, and forgetting regret. |
| 72 | [Build Your Own Harness](curriculum/advanced/end-to-end-eval/index.md) | `govern` | Score multi-session recall, knowledge update, and temporal reasoning on the canonical corpus. |
| 73 | [Regression Testing a Stateful System](curriculum/advanced/regression-testing-state/index.md) | `govern` | Use golden conversations and snapshot tests in CI. |
| 74 | [LLM as Judge, and Its Failure Modes](curriculum/advanced/llm-as-judge-for-memory/index.md) | `govern` | Use model grading where it works and recognise where it does not. |
| 75 | [Reading Benchmark Claims Critically](curriculum/advanced/reading-benchmark-claims/index.md) | `govern` | Interpret public leaderboards, given the same system is cited at wildly different scores. |

**Cost, Latency & Scale**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 76 | [The Write Path Dominates](curriculum/advanced/cost-model/index.md) | `govern` | Price per-turn extraction as the expensive part — the inverse of RAG's cost profile. |
| 77 | [The Latency Budget](curriculum/advanced/latency-budget/index.md) | `govern` | Split synchronous from deferred work along what the user can wait for. |
| 78 | [Caching, Batching, Routing](curriculum/advanced/caching-batching-routing/index.md) | `govern` | Put cheap models on the write path and cache embeddings. |
| 79 | [Scaling the Store](curriculum/advanced/scaling-the-store/index.md) | `store` | Partition by owner; handle index growth, hot users, and archival tiers. |

**Production Failure Modes & Governance**

| # | Lesson | Stage | You will be able to |
|--:|---|---|---|
| 80 | [The Failure Field Guide](curriculum/advanced/failure-field-guide/index.md) | `govern` | Recognise the seven production failure classes by symptom. |
| 81 | [Memory Observability](curriculum/advanced/memory-observability/index.md) | `govern` | Answer 'why did you remember that?' with audit logs and memory diffs. |
| 82 | [Invariants and Drift Detection](curriculum/advanced/invariants-and-drift-detection/index.md) | `govern` | Assert what must always be true of the store and detect when it stops being true. |
| 83 | [Migrating Live Memory](curriculum/advanced/schema-migration-on-live-memory/index.md) | `store` | Evolve the record shape with backfills and history reprocessing. |
| 84 | [Hardening Pass](curriculum/advanced/capstone-finale/index.md) | `govern` | Ship memlab v0.3 with an eval report and a cost profile. |

<!-- generated:end -->
