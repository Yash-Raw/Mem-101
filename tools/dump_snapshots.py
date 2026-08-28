"""Dump every module snapshot, for the before/after diff that proves nothing moved.

    uv run python tools/dump_snapshots.py > before.txt
    <make the change>
    uv run python tools/dump_snapshots.py > after.txt
    diff before.txt after.txt

Covers `@I1`-`@I8` *and* `@A1`-onward. The A-modules were missing from the
ad-hoc version of this script, so every "unchanged" it printed after the Level 3
seams landed was silent about Level 3.
"""
from __future__ import annotations

import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "capstone" / "src"))

from memlab.app.chat import ask, ingest
from memlab.eval.exam import QUESTION, exam_answer
from memlab.pipeline import ADVANCED_MODULES, MODULES, at
from memlab.store.jsonl import JsonlStore
from memlab.temporal.clocks import event_start
from memlab.types import Scope

PRIYA = Scope(user="priya")
LANDED = ("A1", "A2", "A3")  # extend as each Advanced module lands


def main() -> None:
    for module in (*MODULES, *[m for m in ADVANCED_MODULES if m in LANDED]):
        pipeline = at(module)
        store = JsonlStore(pathlib.Path(tempfile.mkdtemp()) / "m.jsonl")
        ingest(store, PRIYA, pipeline)
        if pipeline.vectors is not None:
            pipeline.vectors.index(store.all())
        _ctx, hits = ask(store, PRIYA, QUESTION, k=5, pipeline=pipeline)
        memories = store.all()
        print(
            module,
            len(memories),
            sum(m.is_live for m in memories),
            exam_answer(memories, PRIYA).is_correct,
            sum(1 for m in memories if m.valid_from),
            sum(1 for m in memories if m.valid_to),
            len({m.recorded_at.isoformat() for m in memories}),
            [f"{h.score:.4f}:{h.memory.id}" for h in hits],
            sorted(f"{m.id}:{event_start(m).isoformat()}" for m in memories),
        )


if __name__ == "__main__":
    main()
