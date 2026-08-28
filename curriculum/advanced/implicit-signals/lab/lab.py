"""Lab: read the reaction, not just the claim.

    uv run python curriculum/advanced/implicit-signals/lab/lab.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from memlab.types import Memory

# Deliberately narrow. A broad pattern turns every "no" into a correction --
# including "no meat", which is a dietary fact and not a complaint about the
# assistant. Precision matters more than recall here: a false correction
# demotes a belief that was right.
_CORRECTION = re.compile(
    r"\bremember\?|\bI (?:said|told you)\b|\bthat'?s (?:not|wrong)\b|\bactually,? (?:no|I)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Correction:
    """A user turn rejecting what the assistant just said."""

    session: int
    assistant_said: str
    user_replied: str
    target: Memory | None = None

    @property
    def attributed(self) -> bool:
        return self.target is not None


def corrections(turns: list[dict]) -> list[Correction]:
    """User turns that reject the assistant's immediately preceding turn.

    The pairing is what makes this a *signal* rather than a sentiment: a
    correction with no assistant turn before it is the user changing their
    mind, which is an ordinary write, not evidence that a belief was wrong.
    """
    raise NotImplementedError("implement corrections")


def attribute(correction: Correction, memories: list[Memory]) -> Correction:
    """Find the belief the assistant's turn used.

    Matched on content overlap with the assistant's own words, which is
    available and honest: the assistant said it, so the words are there. A
    retrieval log would be better and this course does not keep one -- which
    is itself the finding, and `memory-observability` is where it lands.
    """
    raise NotImplementedError("implement attribute")


def _keywords(content: str) -> list[str]:
    """Capitalised tokens and long words -- what a sentence is *about*."""
    return [
        w.strip(".,'?").lower()
        for w in content.split()
        if w[:1].isupper() or len(w.strip(".,'?")) > 6
    ]


def used(memories: list[Memory]) -> int:
    """How many beliefs record ever having been retrieved."""
    return sum(1 for m in memories if m.access_count)


STALE = "data engineer at Northwind"


def main() -> None:
    from dataclasses import replace as dc_replace

    import memlab.evolve.dedupe as dedupe_mod
    from memlab.app.chat import _agent_memories, ingest
    from memlab.fixtures import load_turns
    from memlab.pipeline import at
    from memlab.sleep.schedule import Schedule
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    scope = Scope(user="priya")
    pipeline = at("A3")
    user_turns = [t for t in load_turns(user_only=True) if t["session"] < 14]
    every_turn = [t for t in load_turns() if t["session"] < 14]

    store = JsonlStore("/tmp/memlab-signals.jsonl")
    store.clear()
    ingest(store, scope, pipeline)
    print(f"memories recording any use at all:  {used(store.all())} "
          f"of {len(store.all())}\n")

    for correction in corrections(every_turn):
        found = attribute(correction, store.all())
        print(f"   session {correction.session}")
        print(f"      assistant  {correction.assistant_said}")
        print(f"      user       {correction.user_replied}")
        print(f"      target     {found.target.content if found.target else None}")

    # Reference: consolidated after every turn.
    reference, eager = [], JsonlStore("/tmp/memlab-signals-ref.jsonl")
    eager.clear()
    for turn in user_turns:
        memories = pipeline.extract(turn, scope)
        if pipeline.resolve is not None:
            memories = pipeline.resolve(memories, eager.all())
        eager.add(memories)
        eager.replace(pipeline.consolidate(eager.all()))
        reference.append(
            sum(1 for m in eager.all() if m.is_live and STALE in m.content)
        )

    def walk(schedule, act_on_corrections):
        counts = {"embed": 0, "cosine": 0}
        embed, cosine = dedupe_mod.embed_text, dedupe_mod.cosine
        dedupe_mod.embed_text = lambda *a, **k: (
            counts.__setitem__("embed", counts["embed"] + 1), embed(*a, **k))[1]
        dedupe_mod.cosine = lambda *a, **k: (
            counts.__setitem__("cosine", counts["cosine"] + 1), cosine(*a, **k))[1]

        walked = JsonlStore("/tmp/memlab-signals-walk.jsonl")
        walked.clear()
        runs, wrong, acted = 0, 0, set()
        for i, turn in enumerate(user_turns):
            before = walked.all()
            memories = pipeline.extract(turn, scope)
            if pipeline.resolve is not None:
                memories = pipeline.resolve(memories, before)
            walked.add(memories)
            if schedule.needs_inline(memories, before):
                walked.replace(pipeline.consolidate(walked.all()))
                runs += 1
            if act_on_corrections:
                # By timestamp, not by session: session 9 has two user turns and
                # the correction is the second. Filtering by session applies
                # the signal one turn before the user gives it.
                so_far = [t for t in every_turn if t["ts"] <= turn["ts"]]
                for correction in corrections(so_far):
                    if correction.session in acted:
                        continue
                    found = attribute(correction, walked.all())
                    if found.target and found.target.is_live:
                        acted.add(correction.session)
                        walked.replace([
                            dc_replace(m, invalid_at=m.recorded_at,
                                       superseded_by="correction")
                            if m.id == found.target.id else m
                            for m in walked.all()
                        ])
            if sum(1 for m in walked.all()
                   if m.is_live and STALE in m.content) != reference[i]:
                wrong += 1
        walked.add(_agent_memories(scope))
        walked.replace(pipeline.consolidate(walked.all()))
        runs += 1
        dedupe_mod.embed_text, dedupe_mod.cosine = embed, cosine
        return (runs, counts["embed"], counts["cosine"], wrong,
                sum(m.is_live for m in walked.all()))

    print(f"\n   {'policy':38}{'runs':>6}{'embed':>8}{'cosine':>9}"
          f"{'wrong':>7}{'live':>6}")
    for label, schedule, act in (
        ("defer everything", Schedule.never(), False),
        ("consolidate on a contested slot", Schedule.default(), False),
        ("act on corrections, never consolidate", Schedule.never(), True),
    ):
        runs, embed, cosine, wrong, live = walk(schedule, act)
        print(f"   {label:38}{runs:>6}{embed:>8}{cosine:>9}{wrong:>7}{live:>6}")


if __name__ == "__main__":
    main()
