"""Reference solution."""
from __future__ import annotations

from memlab.evolve.summarize import Summary, session_of
from memlab.types import Memory, MemoryType, Provenance, Scope, Tier


def summarise_session(memories: list[Memory], session: str, scope: Scope) -> Summary | None:
    members = [
        m for m in memories
        if session_of(m) == session
        and m.is_live
        and m.type in (MemoryType.SEMANTIC, MemoryType.PROCEDURAL)
    ]
    if len(members) < 2:
        return None

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
    live_ids = {m.id for m in memories if m.is_live}
    return [m for m in memories if m.derived_from and not set(m.derived_from) <= live_ids]
