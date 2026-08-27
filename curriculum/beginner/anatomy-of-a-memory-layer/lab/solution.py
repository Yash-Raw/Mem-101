"""Reference solution: one turn, six boxes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from memlab.assemble.simple import assemble
from memlab.extract.naive import extract
from memlab.retrieve.embedding import EmbeddingRetriever
from memlab.store.jsonl import JsonlStore
from memlab.types import Memory, MemoryType, Scope


def populate_except(store: JsonlStore, scope: Scope, skip_session: int) -> int:
    """Everything else Priya said. A memory only fails by losing to competition."""
    from memlab.fixtures import load_turns

    for turn in load_turns(user_only=True):
        if turn["session"] != skip_session and turn["session"] < 14:
            store.add(extract(turn, scope))
    return len(store.all())


@dataclass
class Stage:
    box: str
    produced: Any
    note: str = ""


@dataclass
class Trace:
    stages: list[Stage] = field(default_factory=list)

    def add(self, box: str, produced: Any, note: str = "") -> None:
        self.stages.append(Stage(box, produced, note))

    def by_box(self, box: str) -> Stage:
        return next(s for s in self.stages if s.box == box)


def resolve(new: list[Memory], existing: list[Memory]) -> tuple[list[Memory], list[str]]:
    """The no-op that reports what it did not do.

    A real resolver would detect that these memories concern a subject already
    in the store and decide update/merge/keep-both. Beginner keeps both, always,
    and this function exists to make that choice visible instead of implicit.
    """
    conflicts = []
    for m in new:
        for e in existing:
            if e.type is MemoryType.SEMANTIC and _same_subject(m, e):
                conflicts.append(f"{e.content!r} vs {m.content!r}")
    return new, conflicts


def _same_subject(a: Memory, b: Memory) -> bool:
    employer = ("Northwind", "Calico")
    return any(k in a.content for k in employer) and any(k in b.content for k in employer)


def trace(turn: dict, store: JsonlStore, scope: Scope, query: str, k: int = 5) -> Trace:
    t = Trace()
    t.add("capture", [turn], f"session {turn['session']}, provenance s{turn['session']}:{turn['ts']}")

    memories = extract(turn, scope)
    kinds = ", ".join(sorted({m.type.value for m in memories})) or "nothing"
    t.add("extract", memories, f"{len(memories)} memories ({kinds})")

    kept, conflicts = resolve(memories, store.all())
    t.add("resolve", kept, f"{len(conflicts)} conflict(s) detected, 0 resolved")

    written = store.add(kept)
    t.add("store", written, f"{written} written, {len(store.all())} total")

    hits = EmbeddingRetriever().search(query, store.all(), scope, k=len(store.all()))
    ranks = {h.memory.id: i for i, h in enumerate(hits, 1)}
    t.add("retrieve", hits, f"this turn's memories ranked: {[ranks[m.id] for m in kept]}")

    context = assemble(hits[:k])
    survived = [m for m in kept if m.content in context]
    t.add("assemble", context, f"{len(survived)} of {len(kept)} survived the budget")
    return t
