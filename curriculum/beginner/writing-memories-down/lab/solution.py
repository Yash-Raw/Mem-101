"""Reference solution."""
from __future__ import annotations

from memlab.store.jsonl import JsonlStore
from memlab.types import Memory


class IdempotentStore(JsonlStore):
    """The real behaviour: a repeated write is a no-op."""

    def add(self, memories: list[Memory]) -> int:
        existing = {m.id for m in self.all()}
        fresh = [m for m in memories if m.id not in existing]
        with self.path.open("a") as fh:
            for m in fresh:
                fh.write(m.to_json() + "\n")
        return len(fresh)


class NaiveStore(JsonlStore):
    """The contrast: appends unconditionally. One redeploy and the store doubles."""

    def add(self, memories: list[Memory]) -> int:
        with self.path.open("a") as fh:
            for m in memories:
                fh.write(m.to_json() + "\n")
        return len(memories)
