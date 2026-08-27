"""Lab: allocation between questions, not just within one.

    uv run python curriculum/intermediate/the-packing-problem/lab/lab.py
"""

from __future__ import annotations

from dataclasses import dataclass

from memlab.assemble.ordering import render
from memlab.assemble.simple import HEADER, estimate_tokens
from memlab.retrieve.embedding import Hit


@dataclass
class Packed:
    text: str
    kept: list[Hit]
    dropped: list[Hit]
    used: int
    budget: int

    @property
    def headroom(self) -> int:
        return self.budget - self.used


def pack(
    hits: list[Hit],
    budget_tokens: int = 400,
    header: str = HEADER,
    suppress_padding: bool = True,
    pin: bool = False,
) -> Packed:
    """Fit what matters. Whole memories only.

    Two passes. The first takes each sub-question's best answer, so no question
    goes unanswered. The second fills with everything else by score -- and when
    `suppress_padding` is on, a question's second and later hits go last,
    because a follow-up to an answered question is worth less than a first
    answer to an unanswered one.
    """
    used = estimate_tokens(header)
    kept: list[Hit] = []

    def fits(hit: Hit) -> bool:
        return used + estimate_tokens(render(hit)) <= budget_tokens

    def take(hit: Hit) -> None:
        nonlocal used
        kept.append(hit)
        used += estimate_tokens(render(hit))

    if pin:
        from memlab.assemble.pinning import required, unpinned

        must = required(hits)
        for hit in must:                  # pass 0 -- slot coverage
            if fits(hit):
                take(hit)
        for hit in unpinned(hits, must):
            if fits(hit):
                take(hit)
        ordered = [h for h in hits if h in kept]
        lines = [render(h) for h in ordered]
        return Packed(
            text=header + "\n" + "\n".join(lines) if lines else "",
            kept=ordered,
            dropped=[h for h in hits if h not in kept],
            used=used,
            budget=budget_tokens,
        )

    # TODO: two passes.
    #   pass 1 -- one answer per sub-question (hit.query), best first
    #   pass 2 -- everything else; when suppress_padding is on, a question's
    #             second and later hits go LAST
    # Use fits() and take(). Never truncate a memory to make it fit.
    raise NotImplementedError("implement the two packing passes")

    ordered = [h for h in hits if h in kept]
    lines = [render(h) for h in ordered]
    text = header + "\n" + "\n".join(lines) if lines else ""
    return Packed(
        text=text,
        kept=ordered,
        dropped=[h for h in hits if h not in kept],
        used=used,
        budget=budget_tokens,
    )


def assemble(hits: list[Hit], budget_tokens: int = 400, header: str = HEADER) -> str:
    return pack(hits, budget_tokens=budget_tokens, header=header).text


def main() -> None:
    from memlab.app.chat import ask, ingest
    from memlab.eval.exam import QUESTION
    from memlab.pipeline import at
    from memlab.store.jsonl import JsonlStore
    from memlab.types import Scope

    NEEDED = ("works at Calico", "does not eat meat", "eats fish", "gluten")
    scope = Scope(user="priya")
    pipeline = at("I7")
    store = JsonlStore("/tmp/memlab-packing.jsonl")
    store.clear()
    ingest(store, scope, pipeline)
    pipeline.vectors.index(store.all())
    _ctx, hits = ask(store, scope, QUESTION, k=5, pipeline=pipeline)

    print("hits, tagged with the sub-question that surfaced them:\n")
    for h in hits:
        print(f"  {h.score:.3f}  [{h.query}]")
        print(f"          {h.memory.content[:52]}")

    def complete(budget, **kw):
        out = pack(hits, budget_tokens=budget, **kw)
        return all(any(n in h.memory.content for h in out.kept) for n in NEEDED)

    print(f"\n{'budget':>7}{'score-order':>13}{'padding last':>15}")
    for b in (80, 77, 70, 67, 60):
        a = "PASS" if complete(b, suppress_padding=False) else "fail"
        c = "PASS" if complete(b, suppress_padding=True) else "fail"
        print(f"{b:>7}{a:>13}{c:>15}")

    print("\nA complete answer costs 77 tokens by score, 67 with padding last.")
    print("The target is 60, and 29 of those tokens are the header.")
    print("Packing is the wrong layer for the rest.")


if __name__ == "__main__":
    main()
