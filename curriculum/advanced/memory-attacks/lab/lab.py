"""Lab: four attacks, three accidental defences, one gap.

    uv run python curriculum/advanced/memory-attacks/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Attack(str, Enum):
    POISONING = "poisoning"
    INJECTION = "injection"
    CROSS_USER = "cross-user read"
    EXTRACTION = "extraction"


@dataclass(frozen=True)
class Defence:
    attack: Attack
    mechanism: str
    built_for: str
    covered: bool
    residual: str


def survey() -> list[Defence]:
    """What stands between each attack and the store, and why it exists."""
    raise NotImplementedError("implement survey")


def uncovered(defences: list[Defence]) -> list[Defence]:
    raise NotImplementedError("implement uncovered")


def accidental(defences: list[Defence]) -> list[Defence]:
    """Defences built for a reason other than security.

    All of them, here. A control that exists as a side effect is a control
    nobody is maintaining as a control -- it will be refactored for the
    reason it was built, by someone who does not know it is load-bearing
    twice.
    """
    raise NotImplementedError("implement accidental")


def main() -> None:
    from datetime import UTC, datetime

    from memlab.agents.authorise import WritePolicy
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.privacy.delete import purge
    from memlab.store.jsonl import JsonlStore
    from memlab.store.scopes import leak_check
    from memlab.types import Memory, MemoryType, Provenance, Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-attacks.jsonl")
    store.clear()
    ingest(store, scope, at("A3"))
    memories = store.all()

    defences = survey()
    print(f"   {'attack':18}{'covered':>9}  defence")
    for d in defences:
        print(f"   {d.attack.value:18}{d.covered!s:>9}  {d.mechanism}")

    print(f"\n   uncovered : {[d.attack.value for d in uncovered(defences)]}")
    covered = sum(1 for d in defences if d.covered)
    print(f"   accidental: {len(accidental(defences))} of {covered} "
          "defences built for another reason")

    policy = WritePolicy.default()
    newest = max((m.happened_at or m.recorded_at) for m in memories)
    rogue = Memory(
        content="Priya works at Meridian",
        type=MemoryType.SEMANTIC,
        scope=Scope(user="priya"),
        happened_at=datetime(2026, 5, 16, tzinfo=UTC),
        provenance=Provenance(source_id="x:1", speaker="travel-agent", authority=0.9),
    )
    print("\n   exercised against the live system:")
    print("      injection : imperatives in the store    "
          f"{sum(1 for m in memories if 'asked to forget' in m.content)}")
    print(f"      cross-user: leak_check(priya)           "
          f"{len(leak_check(memories, scope))}")
    print("      poisoning : impersonating write refused "
          f"{not policy.check(rogue, scope, newest).admitted}")

    target = next(m for m in memories if "Halloway" in m.content)
    kept = purge(target, memories)
    print(f"\n   the deleted record: {target.content}")
    print(f"      its happened_at: {target.happened_at}")
    print("\n   what survives carrying that instant:")
    for m in kept:
        for field, value in (
            ("happened_at", m.happened_at), ("valid_from", m.valid_from),
            ("valid_to", m.valid_to), ("invalid_at", m.invalid_at),
        ):
            if value == target.happened_at:
                print(f"      {field:12} {m.content[:56]}")
    print(f"\n      derived_from pointing at it: "
          f"{sum(1 for m in kept if target.id in m.derived_from)}")


if __name__ == "__main__":
    main()
