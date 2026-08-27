"""The course's headline metric: session 14, answered from the store.

    "where do I work and what should I not eat?"

Correct: Calico Systems; avoid meat and gluten; fish is fine.

This module READS beliefs -- it does not repair them. That distinction is the
whole point. It answers the way the system itself would: by retrieving, then
reading the top-ranked *live semantic* facts. Under the beginner profile the
retired employer is still live and outranks the current one, so this reports
Northwind, which is genuinely what that system believes. Anything cleverer here
would launder a write-path bug into a passing test.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..retrieve.embedding import EmbeddingRetriever
from ..types import Memory, MemoryType, Scope

QUESTION = "where do I work and what should I not eat?"

EMPLOYERS = {"Northwind Labs": ("Northwind",), "Calico Systems": ("Calico",)}


@dataclass
class ExamAnswer:
    employer: str | None = None
    avoid: set[str] = field(default_factory=set)
    permitted: set[str] = field(default_factory=set)
    evidence: dict[str, str] = field(default_factory=dict)

    @property
    def is_correct(self) -> bool:
        return (
            self.employer == "Calico Systems"
            and self.avoid == {"meat", "gluten"}
            and "fish" in self.permitted
        )


def _live_semantic(memories: list[Memory]) -> list[Memory]:
    return [m for m in memories if m.is_live and m.type is MemoryType.SEMANTIC]


def exam_answer(memories: list[Memory], scope: Scope) -> ExamAnswer:
    ranked = EmbeddingRetriever().search(
        QUESTION, memories, scope, k=len(memories), live_only=True
    )
    beliefs = [h.memory for h in ranked if h.memory.type is MemoryType.SEMANTIC]
    answer = ExamAnswer()

    # Employer: whichever live semantic fact the retriever surfaces first.
    for m in beliefs:
        for name, markers in EMPLOYERS.items():
            if any(k in m.content for k in markers):
                answer.employer = name
                answer.evidence["employer"] = m.content
                break
        if answer.employer:
            break

    live = {m.content for m in _live_semantic(memories)}

    if any("does not eat meat" in c or "vegetarian" in c for c in live):
        answer.avoid.add("meat")
    if any("gluten" in c for c in live):
        answer.avoid.add("gluten")

    # Fish is permitted only if the vegetarian claim has been narrowed. While
    # both "is vegetarian" and "eats fish" are live, the system is holding a
    # contradiction and cannot say fish is fine.
    vegetarian_live = any("Priya is vegetarian" in c for c in live)
    eats_fish = any("eats fish" in c or "pescatarian" in c for c in live)
    if eats_fish and not vegetarian_live:
        answer.permitted.add("fish")
        answer.evidence["fish"] = "vegetarian claim narrowed; fish permitted"
    elif vegetarian_live and eats_fish:
        answer.evidence["fish"] = "unresolved: 'is vegetarian' and 'eats fish' both live"

    return answer
