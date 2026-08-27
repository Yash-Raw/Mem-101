"""Rolling summaries, anchored to what they were made from.

A summary is a *derived* memory, and the field that makes it safe is
`derived_from`. Without it a summary is an orphan claim: you cannot tell what
it was built from, cannot rebuild it when a source changes, and cannot delete
it when a source is deleted -- which is the failure `deletion-that-actually-
deletes` is about. You removed the episode; the summary still knows.

Summarisation here is extractive rather than generative. That is not a
simplification for the course's benefit: an extractive summary is composed of
sentences that exist in the store, so every claim in it is traceable to a
source, and it cannot hallucinate. Generative summaries buy fluency and pay for
it in provenance.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..types import Memory, MemoryType, Provenance, Scope, Tier


@dataclass
class Summary:
    memory: Memory
    sources: list[Memory]
    session_total: int = 0   # chars across EVERY memory in the session

    @property
    def compression(self) -> float:
        """Summary size against the whole session, not against what it kept.

        Measured against its own sources a lossless extractive summary scores
        above 1.0 -- it is longer than the parts, because of the joining. That
        is the correct answer to the wrong question. Compression comes from
        what you chose NOT to carry forward, so the denominator has to be
        everything the session contained.
        """
        return len(self.memory.content) / self.session_total if self.session_total else 1.0

    @property
    def dropped(self) -> int:
        return self.session_total - sum(len(m.content) for m in self.sources)


def session_of(memory: Memory) -> str:
    return memory.provenance.source_id.split(":")[0]


def summarise_session(memories: list[Memory], session: str, scope: Scope) -> Summary | None:
    """One summary per session, from that session's durable claims.

    Only semantic and procedural memories are summarised. Episodes are already
    the record of what happened and summarising them loses their timestamps,
    which is the one thing that makes an episode useful.
    """
    members = [
        m for m in memories
        if session_of(m) == session
        and m.is_live
        and m.type in (MemoryType.SEMANTIC, MemoryType.PROCEDURAL)
    ]
    if len(members) < 2:
        return None  # nothing to compress

    claims = "; ".join(m.content for m in members)
    earliest = min(members, key=lambda m: m.happened_at or m.recorded_at)

    session_total = sum(len(m.content) for m in memories if session_of(m) == session)

    summary = Memory(
        content=f"Summary of {session}: {claims}",
        type=MemoryType.SEMANTIC,
        scope=scope,
        provenance=Provenance(source_id=f"summary:{session}", speaker="system"),
        happened_at=earliest.happened_at,
        tier=Tier.LONG_TERM,
        # Every source, by id. This is what makes the summary rebuildable and
        # deletable rather than an orphan claim.
        derived_from=tuple(sorted(m.id for m in members)),
    )
    return Summary(memory=summary, sources=members, session_total=session_total)


def summarise_all(memories: list[Memory], scope: Scope) -> list[Summary]:
    sessions = sorted({session_of(m) for m in memories}, key=lambda s: (len(s), s))
    out = []
    for session in sessions:
        if (s := summarise_session(memories, session, scope)) is not None:
            out.append(s)
    return out


def orphaned_summaries(memories: list[Memory]) -> list[Memory]:
    """Summaries whose sources are no longer all present.

    Run after any deletion. A summary that outlives its sources is stale at
    best and a privacy violation at worst.
    """
    live_ids = {m.id for m in memories if m.is_live}
    return [
        m for m in memories
        if m.derived_from and not set(m.derived_from) <= live_ids
    ]
