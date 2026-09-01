#!/usr/bin/env python3
"""Landscape pages carry an expiry. High-volatility pages fail CI at 180 days.

Three things this has to do besides failing:

* **Say how close the cliff is, on a green run.** The warning window opens 90
  days before a high-volatility page fails, but a warning printed to stdout in
  a passing job is a warning nobody reads. Every run now ends with the next
  expiry, whether or not anything is wrong.
* **Annotate in CI.** Under GitHub Actions a warning is emitted as a
  `::warning file=...::` so it surfaces on the run and in the diff view.
* **Check the volatility value, not just its presence.** `volatility: hgih`
  used to raise KeyError from the threshold lookup -- a crash, not a finding.
"""
from __future__ import annotations

import datetime as dt
import os
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import Problems, landscape

WARN = {"high": 90, "medium": 180, "low": 365}
FAIL = {"high": 180, "medium": 365, "low": 730}


def _warn(rel: str, message: str) -> None:
    """Print for a human, and annotate for the CI run summary."""
    print(f"  warn  {rel}: {message}")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::warning file={rel}::{message}")


def main() -> int:
    p = Problems()
    now = dt.datetime.now(tz=dt.UTC).date()
    today = dt.date.fromisoformat(os.environ.get("MEMLAB_TODAY", now.isoformat()))

    soonest: tuple[int, str] | None = None

    for d in landscape():
        raw = d.meta.get("last_verified")
        if raw is None:
            continue
        vol = d.meta.get("volatility", "high")
        if vol not in FAIL:
            p.add(d.rel, f"volatility: {vol!r} is not one of {', '.join(sorted(FAIL))}")
            continue
        seen = raw if isinstance(raw, dt.date) else dt.date.fromisoformat(str(raw))
        age = (today - seen).days
        left = FAIL[vol] - age
        if age > FAIL[vol]:
            p.add(d.rel, f"last verified {age}d ago (volatility: {vol}) — re-verify or delete")
            continue
        if age > WARN[vol]:
            _warn(d.rel, f"last verified {age}d ago (volatility: {vol}) — "
                         f"fails in {left}d, on {(seen + dt.timedelta(days=FAIL[vol])).isoformat()}")
        if soonest is None or left < soonest[0]:
            soonest = (left, d.rel)

    if soonest is not None:
        left, rel = soonest
        print(f"        (next expiry: {rel} in {left}d)")
    return p.report("freshness")


if __name__ == "__main__":
    raise SystemExit(main())
