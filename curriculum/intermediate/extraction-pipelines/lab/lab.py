"""Lab: one paragraph, and what it does not fix.

    uv run python curriculum/intermediate/extraction-pipelines/lab/lab.py
"""
from __future__ import annotations

from dataclasses import dataclass

from memlab.extract.atomise import atomise
from memlab.extract.gate import passes
from memlab.extract.naive import SCHEMA
from memlab.extract.pipeline import build_messages
from memlab.llm.base import LLMClient
from memlab.types import Memory, MemoryType, Scope


def extract(turn: dict, scope: Scope, client: LLMClient | None = None) -> list[Memory]:
    """TODO: run the four stages.

      1. candidates -- client.complete(build_messages(turn["text"]), SCHEMA)
      2. atomise    -- atomise(content, type) may return more than one fact
      3. gate       -- keep only those passes(memory, turn["text"]) accepts
      4. route      -- the type comes from the candidate

    Exactly one model call. The gate is rules; do not reach for the model again.
    """
    raise NotImplementedError("implement extract")


@dataclass
class ProfileReport:
    name: str
    total: int
    by_type: dict[str, int]
    calico_state_rank: int | None
    northwind_rank: int
    exam_employer: str | None


def compare_profiles(profiles: tuple[str, ...] = ("beginner", "intermediate")) -> list[ProfileReport]:
    from memlab.app.chat import ingest
    from memlab.eval.exam import exam_answer
    from memlab.pipeline import at, get
    from memlab.retrieve.embedding import EmbeddingRetriever
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    reports = []
    for name in profiles:
        store = JsonlStore(f"/tmp/memlab-cmp-{name}.jsonl")
        store.clear()
        ingest(store, scope, get(name) if name == "beginner" else at("I1"))
        memories = store.all()

        hits = EmbeddingRetriever().search("where do I work?", memories, scope, k=len(memories))
        def rank(needle: str, hits: list = hits) -> int | None:
            return next((i for i, h in enumerate(hits, 1) if needle in h.memory.content), None)

        reports.append(
            ProfileReport(
                name=name,
                total=len(memories),
                by_type={t.value: sum(1 for m in memories if m.type is t) for t in MemoryType},
                calico_state_rank=rank("works at Calico Systems"),
                northwind_rank=rank("at Northwind Labs"),
                exam_employer=exam_answer(memories, scope).employer,
            )
        )
    return reports


def main() -> None:
    print(f"{'profile':<14}{'n':>4}  {'sem/epi/proc':<14} {'Calico rank':>12} {'Northwind':>10}  exam")
    for r in compare_profiles():
        types = f"{r.by_type['semantic']}/{r.by_type['episodic']}/{r.by_type['procedural']}"
        calico = r.calico_state_rank if r.calico_state_rank else "absent"
        print(f"{r.name:<14}{r.total:>4}  {types:<14} {calico!s:>12} {r.northwind_rank:>10}  {r.exam_employer}")

    print("\nThe state exists now, and the exam still says Northwind.")
    print("Extraction made the right answer reachable. Nothing has made it win.")


if __name__ == "__main__":
    main()
