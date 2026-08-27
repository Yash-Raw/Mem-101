"""Reference solution: the diagnostic."""
from __future__ import annotations

from dataclasses import dataclass

from memlab.fixtures import load_turns
from memlab.retrieve.embedding import EmbeddingRetriever
from memlab.types import Memory, Scope

QUESTION = "where do I work and what should I not eat?"


def _ingested_turns() -> list[dict]:
    """Session 14 is the question, not a memory -- ingest holds it out."""
    return [t for t in load_turns(user_only=True) if t["session"] < 14]


@dataclass
class Finding:
    n: int
    name: str
    evidence: str
    fixed_by: str


def rank_of(ranked, needle: str) -> int | None:
    return next((i for i, h in enumerate(ranked, 1) if needle in h.memory.content), None)


def diagnose(memories: list[Memory], scope: Scope) -> list[Finding]:
    ranked = EmbeddingRetriever().search(QUESTION, memories, scope, k=len(memories))
    contents = [m.content for m in memories]
    joined = " ".join(contents)
    out: list[Finding] = []

    stale, current = rank_of(ranked, "at Northwind Labs"), rank_of(ranked, "at Calico now")
    out.append(Finding(
        1, "staleness",
        f"dead employer ranks {stale} of {len(ranked)}; the live one ranks {current}",
        "contradiction-detection, supersession-not-deletion",
    ))

    live_pairs = [
        (a, b) for a, b in [
            ("Priya does not drink coffee", "Priya drinks three coffees a day"),
            ("Priya prefers detailed explanations with reasoning", "Priya prefers shorter answers"),
        ] if a in contents and b in contents
    ]
    out.append(Finding(
        2, "contradictions accumulate",
        f"{len(live_pairs)} contradictory pairs, both sides live, nothing superseded",
        "memory-operations, deterministic-freshness",
    ))

    veg, fish = rank_of(ranked, "Priya is vegetarian"), rank_of(ranked, "Priya eats fish")
    linked = sum(1 for m in memories if m.superseded_by is not None)
    out.append(Finding(
        3, "refinement read as noise",
        f"'vegetarian' ranks {veg}, 'eats fish' ranks {fish}, "
        f"{abs(veg - fish)} apart; {linked} of {len(memories)} memories record any "
        "relationship to another",
        "contradiction-detection",
    ))

    aliases = [n for n in ("Sam ", "Samira", "Sammy") if n in joined]
    out.append(Finding(
        4, "entity fragmentation",
        f"{len(aliases)} surface forms for one person: {aliases}; plus an unresolved pronoun",
        "entity-resolution",
    ))

    transient = rank_of(ranked, "completed her first week")
    out.append(Finding(
        5, "over-extraction",
        f"{len(memories)} memories from {len(_ingested_turns())} turns; "
        f"a finished activity ranks {transient}",
        "extraction-quality, salience-scoring",
    ))

    out.append(Finding(
        6, "no forgetting",
        f"salience values in store: {sorted({m.salience for m in memories})}; "
        f"access counts: {sorted({m.access_count for m in memories})}",
        "why-forgetting-is-a-feature, decay-and-tiers",
    ))

    asked = sum(1 for c in contents if "asked to forget" in c)
    pii_left = sum(1 for c in contents if "Halloway Road" in c or "07700" in c)
    retroactive = sum(1 for c in contents if "used to" in c or "before the move" in c.lower())
    out.append(Finding(
        7, "no time model, and deletion not honoured",
        f"{asked} memory records the deletion request while {pii_left} PII memories remain; "
        f"{retroactive} memory describes the past with no event-time to mark it",
        "two-clocks, deletion-that-actually-deletes",
    ))
    return out


def wrong_answers(memories: list[Memory], scope: Scope, k: int = 10) -> list[str]:
    """Which of the four documented wrong answers this store can produce."""
    hits = EmbeddingRetriever().search(QUESTION, memories, scope, k=k)
    text = " ".join(h.memory.content for h in hits)
    wrong = []
    if "Northwind" in text:
        wrong.append("says Northwind Labs (stale employer recalled)")
    if "Priya is vegetarian" in text and "Priya eats fish" not in text:
        wrong.append("says avoid fish (refinement never applied)")
    if "gluten" not in text:
        wrong.append("omits gluten (diet facts collapsed)")
    if "Berlin" in text:
        wrong.append("says Berlin (hearsay promoted to fact)")
    return wrong
