"""memlab -- the whole loop, end to end.

    uv run python -m memlab.app.chat --ingest --ask "where do I work?"
    uv run python -m memlab.app.chat --profile intermediate --ingest --ask "..."

Ingest every turn Priya has ever said, extract facts, store them, then answer a
question using only what was recalled. It survives process restart, because the
store is a file.

Which stages actually run is decided by the profile -- see memlab.pipeline.
Under `beginner` this is the Level 1 system, wrong in seven documented ways.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from ..assemble.simple import assemble
from ..fixtures import load_agent_writes, load_turns
from ..pipeline import Pipeline, beginner, get
from ..retrieve.embedding import EmbeddingRetriever, Hit
from ..store.jsonl import JsonlStore
from ..types import Memory, MemoryType, Provenance, Scope

DEFAULT_STORE = Path.home() / ".memlab" / "memories.jsonl"
FIRST_HELD_OUT_SESSION = 14  # session 14 is the question, not a memory


def _agent_memories(scope: Scope) -> list[Memory]:
    """Memories other agents wrote into shared scope.

    Each row carries its own `authority`: the calendar agent is trusted, the
    travel agent is relaying a colleague's speculation. Keeping that number is
    what lets arbitration demote hearsay instead of believing it.
    """
    from datetime import datetime

    out = []
    for row in load_agent_writes():
        out.append(
            Memory(
                content=row["text"],
                type=MemoryType.SEMANTIC,
                # Filed under the writing agent's namespace, not the user's.
                # Same user, different agent -- which is what makes visibility
                # rules meaningful rather than decorative.
                scope=Scope(user=scope.user, agent=row["agent"]),
                provenance=Provenance(
                    source_id=f"{row['agent']}:{row['ts']}",
                    speaker=row["agent"],
                    authority=row["authority"],
                ),
                happened_at=datetime.fromisoformat(row["ts"]),
            )
        )
    return out


def ingest(
    store: JsonlStore,
    scope: Scope,
    pipeline: Pipeline | None = None,
    before_session: int = FIRST_HELD_OUT_SESSION,
) -> int:
    """Run the write path over the corpus. Returns memories actually written."""
    pipeline = pipeline or beginner()
    added = 0

    for turn in load_turns(user_only=True):
        if turn["session"] >= before_session:
            continue
        memories = pipeline.extract(turn, scope)
        if pipeline.resolve is not None:
            memories = pipeline.resolve(memories, store.all())
        added += store.add(memories)

    if pipeline.ingest_agent_writes:
        added += store.add(_agent_memories(scope))

    if pipeline.consolidate is not None:
        store.replace(pipeline.consolidate(store.all()))

    return added


def ask(
    store: JsonlStore,
    scope: Scope,
    question: str,
    k: int = 5,
    pipeline: Pipeline | None = None,
) -> tuple[str, list[Hit]]:
    pipeline = pipeline or beginner()
    hits = EmbeddingRetriever().search(
        question, store.all(), scope, k=k, live_only=pipeline.live_only
    )
    return assemble(hits), hits


def main() -> None:
    ap = argparse.ArgumentParser(prog="memlab.app.chat")
    ap.add_argument("--store", default=str(DEFAULT_STORE))
    ap.add_argument("--profile", default="beginner", choices=["beginner", "intermediate"])
    ap.add_argument("--ingest", action="store_true", help="rebuild the store from the corpus")
    ap.add_argument("--ask", help="a question to answer from memory")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--user", default="priya")
    args = ap.parse_args()

    pipeline = get(args.profile)
    store, scope = JsonlStore(args.store), Scope(user=args.user)

    if args.ingest:
        store.clear()
        n = ingest(store, scope, pipeline)
        print(f"[{pipeline.name}] ingested {n} memories into {store.path}")

    if args.ask:
        context, hits = ask(store, scope, args.ask, k=args.k, pipeline=pipeline)
        print(f"\nQ: {args.ask}\n")
        print(context or "(nothing recalled)")
        live = len(store.live()) if pipeline.live_only else len(store.all())
        print(f"\n[{len(hits)} of {live} memories recalled, profile={pipeline.name}]")


if __name__ == "__main__":
    main()
