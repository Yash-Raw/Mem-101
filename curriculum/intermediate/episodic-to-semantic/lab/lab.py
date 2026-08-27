"""Lab: the promotion rule that measurement refuses.

    uv run python curriculum/intermediate/episodic-to-semantic/lab/lab.py
"""
from __future__ import annotations

from dataclasses import replace

from memlab.evolve.promote import RELATED_THRESHOLD, Candidate, PromotionReport, session_of
from memlab.llm.fake import cosine, embed_text
from memlab.types import Memory, MemoryType, Scope

# The five pairs the lesson tabulates, with what they actually are.
LABELLED = [
    ("Priya is vegetarian", "Priya is pescatarian", "refinement"),
    ("She works nights most of the month", "Sam still works nights", "corroboration"),
    ("Priya does not drink coffee", "Priya drinks three coffees a day", "contradiction"),
    ("Priya does not eat meat", "Priya eats fish", "compatible"),
]


def subject_of(memory: Memory, scope: Scope) -> frozenset[str]:
    """TODO: who is this belief about?

    Entities if it has them. Otherwise the account holder -- "Priya is
    vegetarian" names nobody and is obviously about Priya. Without the
    fallback, every fact about the user is invisible to this stage.
    """
    raise NotImplementedError("implement subject_of")


def analyse(memories: list[Memory], scope: Scope) -> PromotionReport:
    beliefs = [m for m in memories if m.type is MemoryType.SEMANTIC and m.is_live]
    vectors = {m.id: embed_text(m.content) for m in beliefs}

    candidates: list[Candidate] = []
    for i, a in enumerate(beliefs):
        for b in beliefs[i + 1:]:
            if subject_of(a, scope) != subject_of(b, scope):
                continue
            score = cosine(vectors[a.id], vectors[b.id])
            if score >= RELATED_THRESHOLD:
                candidates.append(
                    Candidate(a=a, b=b, similarity=score,
                              sessions={session_of(a), session_of(b)})
                )

    candidates.sort(key=lambda c: c.similarity, reverse=True)
    return PromotionReport(candidates=candidates, promoted=[])


def corroborate(memory: Memory, supporters: list[Memory]) -> Memory:
    """What promotion looks like once a relationship has been NAMED. Used by I4."""
    return replace(
        memory,
        confidence=min(1.0, memory.confidence + 0.05 * len(supporters)),
        derived_from=tuple(sorted(
            set(memory.derived_from) | {s.provenance.source_id for s in supporters}
        )),
    )


def labelled_scores() -> list[tuple[float, str, str, str]]:
    """Score the pairs whose true relationship we know."""
    out = [
        (cosine(embed_text(a), embed_text(b)), a, b, label)
        for a, b, label in LABELLED
    ]
    return sorted(out, reverse=True, key=lambda t: t[0])


def best_threshold_accuracy() -> float:
    """The best any single cutoff can do at separating corroboration."""
    scored = labelled_scores()
    best = 0.0
    for cut, *_ in scored:
        for delta in (-0.001, 0.001):
            t = cut + delta
            correct = sum(
                1 for s, _, _, label in scored
                if (s >= t) == (label == "corroboration")
            )
            best = max(best, correct / len(scored))
    return best


def main() -> None:
    from memlab.app.chat import ingest
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore

    scope = Scope(user="priya")
    store = JsonlStore("/tmp/memlab-promote.jsonl")
    store.clear()
    ingest(store, scope, at("I3"))

    report = analyse(store.all(), scope)
    print(report.verdict, "\n")

    print("top candidates by similarity:")
    for c in report.candidates[:6]:
        print(f"  {c.similarity:.3f}  {c.a.content[:34]:<34} | {c.b.content[:34]}")

    print("\npairs whose true relationship we know:")
    for score, a, b, label in labelled_scores():
        print(f"  {score:.3f}  [{label:<13}] {a[:32]:<32} | {b[:30]}")

    print(f"\nbest accuracy any single threshold achieves: "
          f"{best_threshold_accuracy():.0%}")
    print("Corroboration sits between a refinement and a contradiction.")
    print("There is no cutoff. This is conflict detection's problem.")


if __name__ == "__main__":
    main()
