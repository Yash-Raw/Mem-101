"""Lab: count the model calls on each path.

    uv run python curriculum/advanced/cost-model/lab/lab.py
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass


@dataclass(frozen=True)
class Cost:
    """Model calls and embeddings for one operation."""

    llm: int
    embed: int

    def per(self, n: int) -> tuple[float, float]:
        return (round(self.llm / n, 1), round(self.embed / n, 1))


@contextmanager
def counting():
    """Count every model call and embedding inside the block.

    Patches the fake client rather than wrapping call sites, because a
    counter you have to remember to add is a counter that misses the call
    somebody added last week.
    """
    raise NotImplementedError("implement counting")
    yield {}


def ratio(write: Cost, read: Cost) -> tuple[str, str]:
    """How much more the write path costs. Division by zero is the point."""
    raise NotImplementedError("implement ratio")


def main() -> None:
    from memlab.app.chat import ask, ingest
    from memlab.eval.exam import QUESTION
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    pipeline = at("A3")
    store = JsonlStore("/tmp/memlab-cost.jsonl")

    with counting() as counts:
        store.clear()
        ingest(store, scope, pipeline)
    write = Cost(**counts)

    pipeline.vectors.index(store.all())
    with counting() as counts:
        ask(store, scope, QUESTION, k=5, pipeline=pipeline)
    read = Cost(**counts)

    llm_ratio, embed_ratio = ratio(write, read)
    print(f"   write path (full ingest, 24 turns)   llm {write.llm:3}   "
          f"embed {write.embed:3}")
    print(f"   read path  (one question)            llm {read.llm:3}   "
          f"embed {read.embed:3}")
    print(f"   ratio                                llm {llm_ratio}   "
          f"embed {embed_ratio}")
    print(f"   per turn                             llm {write.per(24)[0]}   "
          f"embed {write.per(24)[1]}")


if __name__ == "__main__":
    main()
