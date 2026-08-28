"""Reference solution."""

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


# Every module that did `from ..llm.fake import embed_text`. Patching
# `fake.embed_text` alone does NOT reach these -- the import bound the
# function object into each module's namespace, so the counter has to be
# installed in all of them. Miss one and the count is silently low.
_IMPORTERS = (
    "memlab.evolve.dedupe",
    "memlab.evolve.promote",
    "memlab.retrieve.hybrid",
    "memlab.store.vector",
)


@contextmanager
def counting():
    """Count every model call and embedding inside the block.

    Patching the client is necessary and not sufficient: Python's
    `from x import y` copies a reference, so each importing module keeps its
    own binding. `_IMPORTERS` is therefore a list that has to be maintained,
    and a test derives the real set from the source to stop it going stale.
    """
    import importlib

    from memlab.llm import fake

    counts = {"llm": 0, "embed": 0}
    complete, embed = fake.FakeLLM.complete, fake.embed_text

    def counted_complete(self, *args, **kwargs):
        counts["llm"] += 1
        return complete(self, *args, **kwargs)

    def counted_embed(*args, **kwargs):
        counts["embed"] += 1
        return embed(*args, **kwargs)

    modules = [importlib.import_module(name) for name in _IMPORTERS]
    fake.FakeLLM.complete = counted_complete
    fake.embed_text = counted_embed
    for module in modules:
        module.embed_text = counted_embed
    try:
        yield counts
    finally:
        fake.FakeLLM.complete = complete
        fake.embed_text = embed
        for module in modules:
            module.embed_text = embed


def ratio(write: Cost, read: Cost) -> tuple[str, str]:
    """How much more the write path costs. Division by zero is the point."""
    return (
        "no model calls at all" if read.llm == 0 else f"{write.llm / read.llm:.0f}x",
        f"{write.embed / read.embed:.0f}x" if read.embed else "n/a",
    )
