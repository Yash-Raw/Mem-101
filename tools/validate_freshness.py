#!/usr/bin/env python3
"""Landscape pages carry an expiry. High-volatility pages fail CI at 180 days."""
from __future__ import annotations

import datetime as dt
import os
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import Problems, landscape

WARN = {"high": 90, "medium": 180, "low": 365}
FAIL = {"high": 180, "medium": 365, "low": 730}


def main() -> int:
    p = Problems()
    now = dt.datetime.now(tz=dt.UTC).date()
    today = dt.date.fromisoformat(os.environ.get("MEMLAB_TODAY", now.isoformat()))

    for d in landscape():
        raw = d.meta.get("last_verified")
        if raw is None:
            continue
        seen = raw if isinstance(raw, dt.date) else dt.date.fromisoformat(str(raw))
        age = (today - seen).days
        vol = d.meta.get("volatility", "high")
        if age > FAIL[vol]:
            p.add(d.rel, f"last verified {age}d ago (volatility: {vol}) — re-verify or delete")
        elif age > WARN[vol]:
            print(f"  warn  {d.rel}: last verified {age}d ago (volatility: {vol})")

    return p.report("freshness")


if __name__ == "__main__":
    raise SystemExit(main())
