---
id: proof-without-retention
title: "Proof Without Retention"
kind: concept
stage: govern
contrasts_with: [deletion-receipt]
related: [memory-record, deduplication, cascade-deletion]
status: published
---

# Proof Without Retention

Demonstrating that data was destroyed, without keeping a copy of it.

## Why it matters in a memory layer

Every obvious form of evidence is a re-disclosure. A log quoting the content is the content; a "deleted" table is a copy; even confirming the data is gone requires the data to search for. **An audit that needs what was erased has not erased it.**

The way out is a content-addressed id. `Memory.id` has been a truncated SHA-256 of user, type, content and source since Beginner, where it existed for **deduplication** — and it happens to have exactly the property an audit needs: anyone holding the original can verify the receipt describes it, and anyone else learns a hex string.

Proof and disclosure are usually the same operation. This is one of the few places they come apart, and it came apart by accident — a design decision made two levels earlier for an unrelated reason.

## Connections

<!-- graph:begin -->
**Taught in:** [Proving You Forgot](../curriculum/advanced/rtbf-and-auditability/index.md)

**Do not confuse with:** [Deletion Receipt](deletion-receipt.md)
<!-- graph:end -->
