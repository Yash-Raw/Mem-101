"""Lab: answer "why do you think that?" from the record alone.

    uv run python curriculum/advanced/memory-observability/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.types import Memory


@dataclass(frozen=True)
class Explanation:
    """Why one belief is in the store, and what depends on it."""

    memory: Memory
    replaced: tuple[Memory, ...]     # beliefs this one retired
    replaced_by: Memory | None       # the belief that retired this one
    derived: tuple[Memory, ...]      # built from this one
    sources: tuple[Memory, ...]      # this one was built from these

    @property
    def lines(self) -> list[str]:
        m = self.memory
        out = [
            f"content   {m.content}",
            f"source    {m.provenance.source_id}",
            f"speaker   {m.provenance.speaker} (authority {m.provenance.authority})",
            f"true      {_span(m.valid_from or m.happened_at, m.valid_to)}",
            f"believed  {_span(m.recorded_at, m.invalid_at)}",
        ]
        if self.replaced:
            out.append(f"replaced  {len(self.replaced)}: "
                       + "; ".join(x.content for x in self.replaced))
        if self.replaced_by:
            out.append(f"retired by {self.replaced_by.content}")
        if self.derived:
            out.append(f"supports  {len(self.derived)} derived belief(s)")
        return out


def _span(start, end) -> str:
    left = start.date().isoformat() if start else "?"
    return f"{left} .. {end.date().isoformat() if end else 'open'}"


def explain(memory: Memory, memories: list[Memory]) -> Explanation:
    """Reconstruct a belief's history from the record alone."""
    raise NotImplementedError("implement explain")


def unanswerable() -> tuple[str, ...]:
    """Questions the record cannot answer, however carefully it was designed.

    All three need something written down at read time. Listing them is the
    point: an observability story that claims full coverage from provenance
    alone is wrong in a way nobody notices until an incident.
    """
    raise NotImplementedError("implement unanswerable")


def diff(before: list[Memory], after: list[Memory]) -> dict[str, int]:
    """What one write changed about the store, by id."""
    raise NotImplementedError("implement diff")


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.fixtures import load_turns
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    pipeline = at("A3")
    store = JsonlStore("/tmp/memlab-observe.jsonl")
    store.clear()
    ingest(store, scope, pipeline)
    memories = store.all()

    for probe in ("works at Calico", "data engineer at Northwind"):
        found = next(m for m in memories if probe in m.content)
        print(f"   -- {probe}")
        for line in explain(found, memories).lines:
            print(f"      {line}")
        print()

    walk = JsonlStore("/tmp/memlab-observe-walk.jsonl")
    walk.clear()
    turns = [t for t in load_turns(user_only=True) if t["session"] < 14]
    removals = 0
    for i, turn in enumerate(turns, 1):
        before = walk.all()
        written = pipeline.extract(turn, scope)
        if pipeline.resolve is not None:
            written = pipeline.resolve(written, before)
        walk.add(written)
        walk.replace(pipeline.consolidate(walk.all()))
        changed = diff(before, walk.all())
        removals += changed["removed"]
        if i in (1, 14, 18, 22):
            print(f"   turn {i:>2} s{turn['session']:<3} {changed}")

    print(f"\n   removed, summed over every turn: {removals}")
    used = sum(1 for m in memories if m.access_count)
    print(f"   memories recording any use: {used} of {len(memories)}")
    print("\n   not answerable from the record:")
    for question in unanswerable():
        print(f"      {question}")


if __name__ == "__main__":
    main()
