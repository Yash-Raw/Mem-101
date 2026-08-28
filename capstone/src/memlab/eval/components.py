"""Scoring the stages, instead of scoring through them.

`why-memory-eval-is-hard` counted seven stages between a turn and an answer,
and one boolean over all of them. Component metrics give each stage a number
against `gold.yml` -- which is possible for four of the seven and not for
three, and the split is the interesting part.

    extract     precision/recall against what gold says should be there
    resolve     did the surface forms reach one canonical id?
    arbitrate   is the live value the one gold says is current?
    anchor      do the parsed dates match gold's dates?

    dedupe      no gold entry: nobody wrote down which pairs are duplicates
    decay       no gold entry: "should have faded" is not a fact about a turn
    rank        no gold entry: relevance judgements are the thing memory eval
                lacks by construction

The three that cannot be scored are not an oversight in the answer key. They
are the stages whose correct behaviour is a *policy*, not a fact about the
conversation -- and a gold entry for them would be a restatement of whatever
policy was implemented.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..evolve.conflict import slot_of
from ..fixtures import load_gold
from ..temporal.clocks import event_start
from ..types import Memory, MemoryType, Scope


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
    wanted = [s["value"] for s in load_gold()["pii"]]
    found = sum(
        1
        for w in wanted
        if any(w.split(",")[0].lower() in m.content.lower() for m in memories)
    )
    return Metric("extract", found, len(wanted))


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
    entries = [s for s in load_gold()["supersessions"] if "replacement" in s]
    right = unmatched = 0
    for entry in entries:
        session = f"s{entry['original']['session']}:"
        claims = [
            m
            for m in memories
            if m.type is MemoryType.SEMANTIC
            and m.provenance.source_id.startswith(session)
            and slot_of(m) == entry["subject"]
        ]
        retired = [m for m in claims if not m.is_live]
        if not retired:
            # Two ways to land here, and neither is the arbitrator failing.
            # `commute` names session 11, where the only claim in that slot
            # is the *replacement* -- the system represents the change as a
            # past-tense statement rather than a supersession, which is
            # defensible. Scoring that as wrong measures the answer key's
            # model of the change, not the system's handling of it.
            unmatched += 1
        else:
            right += 1
    return Metric("arbitrate", right, len(entries), unmatched)


def anchoring(memories: list[Memory]) -> Metric:
    """Do parsed event dates match the dates gold gives for each phrase?

    Matching on the phrase alone picks the *first* memory containing it, and
    "last week" appears in two -- the gluten diagnosis and a step inside the
    weekly-report procedure. Gold gives a session for every entry precisely
    so the lookup can be unambiguous, and ignoring it scored 0.500 against a
    parser that was right.
    """
    entries = [
        e
        for e in load_gold()["relative_time"]
        if e["resolves_to"] and isinstance(e["session"], int)
    ]
    right = unmatched = 0
    for entry in entries:
        phrase = entry["phrase"].lower()
        written_by = entry.get("written_by")
        prefix = f"{written_by}:" if written_by else f"s{entry['session']}:"
        found = next(
            (
                m
                for m in memories
                if phrase in m.content.lower()
                and m.provenance.source_id.startswith(prefix)
            ),
            None,
        )
        if found is None:
            unmatched += 1
            continue
        got = event_start(found).date() if event_start(found) else None
        if got == entry["resolves_to"]:
            right += 1
    return Metric("anchor", right, len(entries), unmatched)


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
