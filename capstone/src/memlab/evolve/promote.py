"""Why promotion has to wait for conflict detection.

The tempting rule: a claim restated across sessions is better supported, so
raise its confidence. It is cheap, it needs no model, and it is wrong.

Measured on Priya's store, with cosine over memory content:

    0.669  refinement     "is vegetarian"            / "is pescatarian"
    0.505  CORROBORATION  "She works nights..."      / "Sam still works nights"
    0.439  contradiction  "does not drink coffee"    / "drinks three coffees a day"
    0.412  compatible     "does not eat meat"        / "eats fish"
    0.250  refinement     "Sam is a nurse"           / "Samira is a charge nurse"

There is no threshold. The genuine corroboration sits at 0.505, *below* a
refinement at 0.669 and above a contradiction at 0.439. Any cutoff that
promotes the real one also promotes a refinement, and any cutoff that excludes
the contradiction also excludes the corroboration.

This is `embedding-recall`'s finding again -- similarity measures aboutness, not
agreement -- with the stakes raised. There it produced bad rankings; here it
would produce *confidence*, which is worse: the system would grow more certain
of the facts it should be doubting.

So `promote` promotes nothing on similarity alone. It surfaces candidates and
defers every one of them to conflict detection, which is the only machinery
that can name what the relationship actually is. That deferral is the design,
not a limitation of this implementation.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from ..llm.fake import cosine, embed_text
from ..types import Memory, MemoryType, Scope

# Two beliefs about one subject, close enough to stand in some relationship.
# Deliberately NOT a promotion threshold -- see the module docstring.
RELATED_THRESHOLD = 0.35


@dataclass
class Candidate:
    a: Memory
    b: Memory
    similarity: float
    sessions: set[str]

    @property
    def independent(self) -> bool:
        return len(self.sessions) > 1


@dataclass
class PromotionReport:
    candidates: list[Candidate]
    promoted: list[Memory]

    @property
    def verdict(self) -> str:
        return (
            f"{len(self.candidates)} candidate pairs, {len(self.promoted)} promoted -- "
            "similarity cannot distinguish corroboration from refinement or "
            "contradiction, so all of them defer to conflict detection"
        )


def session_of(memory: Memory) -> str:
    return memory.provenance.source_id.split(":")[0]


def subject_of(memory: Memory, scope: Scope) -> frozenset[str]:
    """Who a belief is about.

    A memory with no linked entity is about the account holder -- "Priya is
    vegetarian" names nobody because `Priya` is on the stop list, and it is
    still a claim about her. Without this, the system can only reason about
    third parties and is blind to every fact about its own user.
    """
    return frozenset(memory.entities) or frozenset({scope.user})


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
    # Nothing is promoted. See the module docstring: the measurement says this
    # signal cannot carry the decision.
    return PromotionReport(candidates=candidates, promoted=[])


def promote(memories: list[Memory], scope: Scope) -> list[Memory]:
    """A no-op that records what it declined to do.

    Kept as a real stage so `contradiction-detection` has somewhere to plug in,
    and so the deferral is visible in the pipeline rather than implied by an
    absence.
    """
    return list(memories)


def corroborate(memory: Memory, supporters: list[Memory]) -> Memory:
    """What promotion looks like ONCE a relationship has been named.

    Used by I4 after conflict detection classifies a pair as a restatement.
    Confidence rises, and the supporting sources are recorded so the boost can
    be traced -- and undone if a supporter is later retired.
    """
    return replace(
        memory,
        confidence=min(1.0, memory.confidence + 0.05 * len(supporters)),
        derived_from=tuple(sorted(
            set(memory.derived_from) | {s.provenance.source_id for s in supporters}
        )),
    )
