"""Lab: compression is what you throw away.

    uv run python curriculum/intermediate/summarization-and-compaction/lab/lab.py
"""
from __future__ import annotations

from memlab.evolve.summarize import Summary, session_of
from memlab.types import Memory, Scope


def summarise_session(memories: list[Memory], session: str, scope: Scope) -> Summary | None:
    """TODO: build one summary from a session's SEMANTIC and PROCEDURAL claims.

    Return None if fewer than two -- nothing to compress.

    The field that matters is `derived_from`: every source memory's id. Without
    it the summary cannot be rebuilt when a source changes, or deleted when a
    source is deleted.

    Set `session_total` to the character count of EVERY memory in the session,
    including the episodes you are dropping. That denominator is where the
    compression actually comes from.
    """
    raise NotImplementedError("implement summarise_session")


def summarise_all(memories: list[Memory], scope: Scope) -> list[Summary]:
    sessions = sorted({session_of(m) for m in memories}, key=lambda s: (len(s), s))
    out = []
    for session in sessions:
        if (s := summarise_session(memories, session, scope)) is not None:
            out.append(s)
    return out


def orphaned_summaries(memories: list[Memory]) -> list[Memory]:
    """TODO: summaries whose sources are no longer all live.

    Run this after any deletion. A summary that outlives its sources is stale
    at best and a privacy violation at worst.
    """
    raise NotImplementedError("implement orphaned_summaries")


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import get
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-summarise.jsonl")
    store.clear()
    ingest(store, scope, get("intermediate"))
    memories = store.all()

    summaries = summarise_all(memories, scope)
    print(f"{len(summaries)} summaries from {len(memories)} memories\n")
    print(f"{'session':<12}{'kept':>6}{'dropped':>10}{'compression':>14}")
    for s in summaries:
        flag = "  <-- EXPANDED" if s.compression > 1 else ""
        print(f"{s.memory.provenance.source_id:<12}{len(s.sources):>6}"
              f"{s.dropped:>10}{s.compression:>14.2f}{flag}")

    before = sum(len(m.content) for m in memories)
    after = sum(len(s.memory.content) for s in summaries)
    print(f"\nwhole store: {before} -> {after} chars ({after / before:.2f})")

    # Delete a source; the summary that used it must be detectable.
    victim = summaries[0].sources[0]
    survivors = [m for m in memories if m.id != victim.id] + [s.memory for s in summaries]
    orphans = orphaned_summaries(survivors)
    print(f"\ndeleted {victim.content[:44]!r}")
    print(f"  -> {len(orphans)} orphaned summary detected")


if __name__ == "__main__":
    main()
