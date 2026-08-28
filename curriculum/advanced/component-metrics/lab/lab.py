"""Lab: score the stages, and debug the metric before the system.

    uv run python curriculum/advanced/component-metrics/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.evolve.conflict import slot_of
from memlab.fixtures import load_gold
from memlab.types import Memory, Scope


@dataclass(frozen=True)
class Metric:
    """A stage's score, and how much of the answer key it could even locate.

    `unmatched` is the field that stops this lying. A metric that cannot find
    the record an entry refers to has learned nothing about the system, and
    folding those into the denominator reports them as failures -- which is
    how the first version of this file scored a working parser at 0.500.
    """

    stage: str
    scored: int
    total: int
    unmatched: int = 0
    scorable: bool = True
    note: str = ""

    @property
    def rate(self) -> float | None:
        """Correct / located. Entries that could not be located are excluded."""
        located = self.total - self.unmatched
        if not self.scorable or not located:
            return None
        return round(self.scored / located, 3)


def extraction(memories: list[Memory]) -> Metric:
    """Are the facts gold names actually in the store?

    Scored against `pii` only, because those entries quote the corpus
    literally. The `supersessions` values are *paraphrases* -- gold says
    "wants short answers" and the store holds "Priya prefers shorter
    answers" -- so matching them as substrings scores the answer key's prose
    style, not the extractor. That is the first thing this metric got wrong,
    and it reported 0.733 while nothing was broken.

    Recall only. Precision would need gold to enumerate everything that
    should *not* be extracted, which is an infinite set -- `over-extraction`
    measured the problem and named no boundary, because there isn't one.
    """
    raise NotImplementedError("implement extraction")


def resolution(memories: list[Memory]) -> Metric:
    """Do gold's surface forms all reach one canonical entity id?"""
    entity = load_gold()["entities"][0]
    forms = [f for f in entity["surface_forms"] if f[0].isupper()]
    ids = {
        e
        for form in forms
        for m in memories
        if form in m.content
        for e in m.entities
    }
    return Metric("resolve", 1 if len(ids) == 1 else 0, 1)


def arbitration(memories: list[Memory], scope: Scope) -> Metric:
    """Is *a* belief in the superseded slot actually retired?

    Not "are all of them". `beverage` names session 4, which holds two
    claims in that slot -- "does not drink coffee", correctly retired, and
    "drinks tea", correctly still live. Requiring every claim from the
    session to be retired scores the fact that she still drinks tea as an
    arbitration failure.

    Located by SESSION, not by value. Gold's supersession values are
    paraphrases -- "wants short answers" for "Priya prefers shorter answers"
    -- so a substring match scores the answer key's prose. The session is
    unambiguous and is why every entry carries one.
    """
    raise NotImplementedError("implement arbitration")


def anchoring(memories: list[Memory]) -> Metric:
    """Do parsed event dates match the dates gold gives for each phrase?

    Matching on the phrase alone picks the *first* memory containing it, and
    "last week" appears in two -- the gluten diagnosis and a step inside the
    weekly-report procedure. Gold gives a session for every entry precisely
    so the lookup can be unambiguous, and ignoring it scored 0.500 against a
    parser that was right.
    """
    raise NotImplementedError("implement anchoring")


def unscorable() -> list[Metric]:
    """The stages whose correct behaviour is a policy, not a fact."""
    return [
        Metric("dedupe", 0, 0, 0, False,
               "which pairs are duplicates is a threshold, not a fact"),
        Metric("decay", 0, 0, 0, False,
               "'should have faded' is not a fact about a turn"),
        Metric("rank", 0, 0, 0, False,
               "relevance judgements are what memory eval lacks by construction"),
    ]


def report(memories: list[Memory], scope: Scope) -> list[Metric]:
    return [
        extraction(memories),
        resolution(memories),
        arbitration(memories, scope),
        anchoring(memories),
        *unscorable(),
    ]


def _slots(memories: list[Memory]) -> set[str]:
    return {slot_of(m) for m in memories if slot_of(m)}


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-components.jsonl")
    store.clear()
    ingest(store, scope, at("A3"))

    print(f"   {'stage':12}{'correct':>9}{'located':>9}{'entries':>9}{'rate':>8}  note")
    for metric in report(store.all(), scope):
        rate = f"{metric.rate:.3f}" if metric.rate is not None else "--"
        print(f"   {metric.stage:12}{metric.scored:>9}"
              f"{metric.total - metric.unmatched:>9}{metric.total:>9}"
              f"{rate:>8}  {metric.note[:44]}")

    folded = []
    for metric in report(store.all(), scope):
        if metric.scorable and metric.total:
            folded.append((metric.stage, round(metric.scored / metric.total, 3)))
    print(f"\n   the same numbers with unmatched folded in: {folded}")


if __name__ == "__main__":
    main()
