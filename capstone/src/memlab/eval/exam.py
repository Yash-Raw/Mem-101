"""The course's headline metric: session 14, answered from the store.

    "where do I work and what should I not eat?"

Correct: Calico Systems; avoid meat and gluten; fish is fine.

There are two readers, and the gap between them is the point.

`exam_answer` reads the whole live belief store: it asks whether the system
BELIEVES the right thing. `exam_from_context` reads only the assembled context
at a realistic k: it asks whether the system would SAY it. A store can be
entirely correct and still fail the second one, because ranking is a separate
problem from belief -- which is exactly the state Milestone 2a left things in.

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


def exam_from_context(
    memories: list[Memory],
    scope: Scope,
    k: int = 5,
    pipeline=None,
) -> ExamAnswer:
    """Answer from ONLY what the model receives.

    The stricter reader. `exam_answer` may scan thirty beliefs; a model sees
    whatever survived top-k and the token budget. Holding a correct belief that
    never reaches the context is not answering the question -- it is being right
    somewhere the user cannot see.
    """
    from ..app.chat import ask
    from ..store.jsonl import JsonlStore

    class _View(JsonlStore):
        """Adapt an in-memory list to the store interface `ask` expects."""

        def __init__(self, items: list[Memory]) -> None:
            self._items = items

        def all(self) -> list[Memory]:
            return self._items

        def live(self) -> list[Memory]:
            return [m for m in self._items if m.is_live]

    context, _hits = ask(_View(memories), scope, QUESTION, k=k, pipeline=pipeline)

    answer = ExamAnswer()
    for name, markers in EMPLOYERS.items():
        if any(marker in context for marker in markers):
            answer.employer = name
            answer.evidence["employer"] = "found in assembled context"
            break

    if "does not eat meat" in context or "vegetarian" in context:
        answer.avoid.add("meat")
    if "gluten" in context:
        answer.avoid.add("gluten")
    if ("eats fish" in context or "pescatarian" in context) and "is vegetarian" not in context:
        answer.permitted.add("fish")

    answer.evidence["context_lines"] = str(context.count("\n- "))
    return answer
