"""Lab: retire, do not destroy.

    uv run python curriculum/intermediate/supersession-not-deletion/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from memlab.evolve.conflict import detect
from memlab.evolve.operations import Decision, Operation, decide_all
from memlab.evolve.promote import corroborate
from memlab.types import Memory, Scope


@dataclass
class Reconciliation:
    memories: list[Memory]
    decisions: list[Decision]

    @property
    def retired(self) -> list[Memory]:
        return [m for m in self.memories if not m.is_live]

    def summary(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for d in self.decisions:
            out[d.operation.value] = out.get(d.operation.value, 0) + 1
        return out


def _when(memory: Memory) -> datetime:
    return memory.happened_at or memory.recorded_at


def reconcile(memories: list[Memory], scope: Scope) -> Reconciliation:
    """TODO: detect, decide, and APPLY.

    For each UPDATE, retire the loser with memory.supersede(by=..., at=...).
    The date is the WINNER's event time -- the belief stopped being true when
    its replacement became true, not when this job happened to run.

    For each MERGE, corroborate the winner with its supporters.

    Nothing is deleted. Nothing episodic is touched -- can_contradict already
    guaranteed episodes never became candidates.
    """
    raise NotImplementedError("implement reconcile")


def reconcile_by_deleting(memories: list[Memory], scope: Scope) -> list[Memory]:
    """The wrong way, for contrast. Passes the exam; loses the history."""

    doomed = {
        d.verdict.loser.id
        for d in decide_all(detect(memories, scope))
        if d.operation is Operation.UPDATE and d.verdict
    }
    return [m for m in memories if m.id not in doomed]


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.eval.exam import exam_answer
    from memlab.pipeline import at, get
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-supersede.jsonl")
    store.clear()
    ingest(store, scope, at("I3"))

    result = reconcile(store.all(), scope)
    print("operations:", result.summary())
    print(f"\n{len(result.retired)} retired, 0 deleted:\n")
    for m in result.retired:
        print(f"  {m.invalid_at.date()}  {m.content[:54]}")

    print("\n\nTHE EXAM: where do I work and what should I not eat?\n")
    print(f"  {'profile':<10}{'live':>6}  {'employer':<18}{'fish ok?':>9}")
    for name, pipeline in [("beginner", get("beginner")), ("@I1", at("I1")),
                           ("@I2", at("I2")), ("@I3", at("I3")), ("@I4", at("I4"))]:
        s = JsonlStore(f"/tmp/memlab-exam-{name}.jsonl")
        s.clear()
        ingest(s, scope, pipeline)
        answer = exam_answer(s.all(), scope)
        live = sum(1 for m in s.all() if m.is_live)
        mark = "   <-- CORRECT" if answer.is_correct else ""
        print(f"  {name:<10}{live:>6}  {answer.employer!s:<18}"
              f"{'fish' in answer.permitted!s:>9}{mark}")

    history = [m for m in result.memories if not m.is_live and "Northwind" in m.content]
    print(f"\n'where did I work before Calico?' -> {history[0].content}")
    print("Still there. That is the difference from deleting.")


if __name__ == "__main__":
    main()
