"""Answering "why do you think that?" from what the record already carries.

`implicit-signals` needed a retrieval log and found none. `deletion-that-
actually-deletes` needed to know which structures held a value and had to be
told. Both are observability gaps, and the interesting thing is how much of
the answer is already in the record without any logging at all.

For any belief the store holds, `explain` reconstructs:

    where it came from      provenance.source_id -- the exact turn
    who said it             provenance.speaker, and their authority
    when it was true        valid_from .. valid_to
    when it was believed    recorded_at .. invalid_at
    what it replaced        superseded_by, followed backwards
    what was built on it    derived_from, followed forwards

Six answers, no log. That is what `the-memory-record` bought by carrying
provenance and two clocks, and what `supersession-not-deletion` bought by
retiring rather than destroying -- the chain is walkable because nothing on
it was ever removed.

What no log can reconstruct is what was *in the context* when the assistant
spoke. That needs writing something down at read time, and this module says
so rather than pretending the record covers it.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..types import Memory


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
    by_id = {m.id: m for m in memories}
    return Explanation(
        memory=memory,
        replaced=tuple(m for m in memories if m.superseded_by == memory.id),
        replaced_by=by_id.get(memory.superseded_by or ""),
        derived=tuple(m for m in memories if memory.id in m.derived_from),
        sources=tuple(by_id[i] for i in memory.derived_from if i in by_id),
    )


def unanswerable() -> tuple[str, ...]:
    """Questions the record cannot answer, however carefully it was designed.

    All three need something written down at read time. Listing them is the
    point: an observability story that claims full coverage from provenance
    alone is wrong in a way nobody notices until an incident.
    """
    return (
        "which memories were in the context when the assistant said that?",
        "how often has this belief actually been used?",
        "which query surfaced it?",
    )


def diff(before: list[Memory], after: list[Memory]) -> dict[str, int]:
    """What one write changed about the store, by id."""
    old, new = {m.id: m for m in before}, {m.id: m for m in after}
    return {
        "added": len(new.keys() - old.keys()),
        "removed": len(old.keys() - new.keys()),
        "retired": sum(
            1 for i in old.keys() & new.keys()
            if old[i].is_live and not new[i].is_live
        ),
    }
