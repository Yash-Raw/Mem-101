"""Lab: change the record shape under a store that must keep working.

    uv run python curriculum/advanced/schema-migration-on-live-memory/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.types import Memory


@dataclass(frozen=True)
class Compatibility:
    """Why a shape change did or did not require rewriting the store."""

    rule: str
    holds: bool
    consequence: str


def compatibility(old: Memory, new: Memory) -> list[Compatibility]:
    """Check a proposed record change against the four rules.

    `old` and `new` are the same memory before and after the change, which is
    the only comparison that answers the question -- a schema diff cannot see
    whether the id moved.
    """
    raise NotImplementedError("implement compatibility")


@dataclass(frozen=True)
class Backfill:
    """A reprocessing pass over history, and what it changed."""

    considered: int
    updated: int
    unchanged: int

    @property
    def restartable(self) -> bool:
        """Re-running must change nothing the second time."""
        return True


def backfill(memories: list[Memory], anchor) -> tuple[list[Memory], Backfill]:
    """Reprocess history through a parser the records predate.

    Idempotent by construction: the parser writes `valid_from` from content,
    so a second pass computes the same value. That is what makes it safe to
    restart, and it is the same property `background-job-mechanics` needed
    from consolidation.
    """
    raise NotImplementedError("implement backfill")
    return out, Backfill(
        considered=len(memories),
        updated=updated,
        unchanged=len(memories) - updated,
    )


def strip(memories: list[Memory]) -> list[Memory]:
    """The store as it looked before the fields existed."""
    raise NotImplementedError("implement strip")


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.temporal.anchor import anchor_all
    from memlab.types import Scope

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-migrate.jsonl")
    store.clear()
    ingest(store, scope, at("A3"))
    current = store.all()
    before = strip(current)

    after = next(m for m in current if "before the move" in m.content)
    prior = next(m for m in before if m.id == after.id)

    print(f"   {'rule':34}{'holds':>7}  consequence")
    for rule in compatibility(prior, after):
        print(f"   {rule.rule:34}{rule.holds!s:>7}  {rule.consequence[:44]}")

    filled, report = backfill(before, anchor_all)
    print(f"\n   backfill: considered {report.considered}  "
          f"updated {report.updated}  unchanged {report.unchanged}")
    _again, second = backfill(filled, anchor_all)
    print(f"   re-run  : updated {second.updated}  "
          f"(restartable={report.restartable})")
    print(f"   ids unchanged by the migration: "
          f"{[m.id for m in before] == [m.id for m in current]}")


if __name__ == "__main__":
    main()
