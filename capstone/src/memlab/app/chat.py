"""memlab v0.1 -- the whole loop, end to end.

    uv run python -m memlab.app.chat --ingest --ask "where do I work?"

Ingest every turn Priya has ever said, extract facts, store them, then answer a
question using only what was recalled. It survives process restart, because the
store is a file.

It is also wrong in seven documented ways, which is the point of the level.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from ..assemble.simple import assemble
from ..extract.naive import extract
from ..fixtures import load_turns
from ..llm.base import get_client
from ..retrieve.embedding import EmbeddingRetriever
from ..store.jsonl import JsonlStore
from ..types import Scope

DEFAULT_STORE = Path.home() / ".memlab" / "memories.jsonl"


def ingest(store: JsonlStore, scope: Scope, before_session: int = 14) -> int:
    client = get_client()
    added = 0
    for turn in load_turns(user_only=True):
        if turn["session"] >= before_session:
            continue
        added += store.add(extract(turn, scope, client))
    return added


def ask(store: JsonlStore, scope: Scope, question: str, k: int = 5) -> tuple[str, list]:
    hits = EmbeddingRetriever().search(question, store.all(), scope, k=k)
    return assemble(hits), hits


def main() -> None:
    ap = argparse.ArgumentParser(prog="memlab.app.chat")
    ap.add_argument("--store", default=str(DEFAULT_STORE))
    ap.add_argument("--profile", default="beginner", choices=["beginner", "intermediate", "advanced"])
    ap.add_argument("--ingest", action="store_true", help="rebuild the store from the corpus")
    ap.add_argument("--ask", help="a question to answer from memory")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--user", default="priya")
    args = ap.parse_args()

    if args.profile != "beginner":
        raise SystemExit(f"profile '{args.profile}' arrives later in the course")

    store, scope = JsonlStore(args.store), Scope(user=args.user)

    if args.ingest:
        store.clear()
        n = ingest(store, scope)
        print(f"ingested {n} memories into {store.path}")

    if args.ask:
        context, hits = ask(store, scope, args.ask, k=args.k)
        print(f"\nQ: {args.ask}\n")
        print(context or "(nothing recalled)")
        print(f"\n[{len(hits)} of {len(store.all())} memories recalled]")


if __name__ == "__main__":
    main()
