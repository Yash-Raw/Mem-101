"""Reference solution."""

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
    precision: str = "dated",
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

    if used > budget_tokens:
        # A header with no memories under it is worse than nothing: it tells the
        # model it has recalled something and then shows it nothing.
        return Packed(text="", kept=[], dropped=list(hits), used=0, budget=budget_tokens)

    def fits(hit: Hit) -> bool:
        return used + estimate_tokens(render(hit, precision)) <= budget_tokens

    def take(hit: Hit) -> None:
        nonlocal used
        kept.append(hit)
        used += estimate_tokens(render(hit, precision))

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
        lines = [render(h, precision) for h in ordered]
        return Packed(
            text=header + "\n" + "\n".join(lines) if lines else "",
            kept=ordered,
            dropped=[h for h in hits if h not in kept],
            used=used,
            budget=budget_tokens,
        )

    answered: set[str] = set()
    padding: list[Hit] = []

    for hit in hits:                      # pass 1 -- one answer per question
        key = hit.query or ""
        if key in answered:
            padding.append(hit)
            continue
        answered.add(key)
        if fits(hit):
            take(hit)

    rest = padding if suppress_padding else [h for h in hits if h not in kept]
    for hit in rest:                      # pass 2 -- fill
        if hit not in kept and fits(hit):
            take(hit)

    ordered = [h for h in hits if h in kept]
    lines = [render(h, precision) for h in ordered]
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
