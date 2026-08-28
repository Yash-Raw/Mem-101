---
id: personal-data
title: "Personal Data"
kind: concept
stage: govern
contrasts_with: [memory-record]
related: [label-not-permission, entity-resolution, redaction]
status: published
---

# Personal Data

Memories carrying information about an identifiable person — including people who are not the account holder.

## Why it matters in a memory layer

In a retrieval system PII is handled upstream: the corpus was assembled and redacted before indexing, and the read path inherits that decision. A memory layer **manufactures its corpus one turn at a time, from the person the data is about, who is telling you on purpose.** There is no upstream to defer to.

Which is why the obvious policy fails. On this course's corpus **7 of 37** memories carry personal data, and blocking all of it drops the gluten intolerance — health data, and one of the four facts the exam requires. Safety that removes the function is not a trade-off; it is one nobody measured.

Three of the seven are about the user's partner, detected by the `entities` link rather than by wording — *"Sam is a nurse"* and *"I am a nurse"* have the same shape and different consent stories. Those three are the easiest to justify blocking and the ones nobody proposes: they cost the user nothing and protect someone who is not in the room.

## Connections

<!-- graph:begin -->
**Taught in:** [PII on the Write Path](../curriculum/advanced/pii-on-the-write-path/index.md)

**Used in:** [Deletion That Actually Deletes](../curriculum/advanced/deletion-that-actually-deletes/index.md) · [Redaction and Minimization](../curriculum/advanced/redaction-and-minimization/index.md)

**Do not confuse with:** [The Memory Record](memory-record.md)
<!-- graph:end -->
