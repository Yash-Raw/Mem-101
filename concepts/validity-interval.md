---
id: validity-interval
title: "Validity Interval"
kind: concept
stage: store
contrasts_with: [supersession]
related: [bi-temporal-modeling, as-of-query, event-time]
status: published
---

# Validity Interval

The span over which a fact was true — `valid_from` to `valid_to` — as distinct from the span over which the system believed it.

## Why it matters in a memory layer

An open `valid_to` means *"still true as far as anyone said"*, and that is the honest default: nothing in a conversation announces that a fact has ended. Closing the interval is a separate act from retiring the belief, and the two dates are routinely different — she left the job in December and mentioned it in January.

Skip the interval and *"what is true now?"* has to be answered by proxy, usually by filtering on belief time. On this course's corpus that proxy returns **five** employer facts where four are live, because without recorded ends every fact stays open. The proxy works only while the two clocks are the same, which is exactly when nobody notices it is a proxy.

## Connections

<!-- graph:begin -->
**Taught in:** [Validity Intervals](../curriculum/advanced/validity-intervals/index.md)

**Used in:** [Three Temporal Questions](../curriculum/advanced/temporal-questions/index.md)

**Do not confuse with:** [Supersession](supersession.md)
<!-- graph:end -->
