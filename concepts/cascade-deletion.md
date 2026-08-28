---
id: cascade-deletion
title: "Cascade Deletion"
kind: concept
stage: govern
contrasts_with: [supersession]
related: [request-resolution, derivation-graph, personal-data]
status: published
---

# Cascade Deletion

Removing a memory from every structure that holds it or derives from it — and proving that it happened.

## Why it matters in a memory layer

Deleting a document from an index is total by construction: drop the row, drop its postings, and every derived structure rebuilds from a corpus that is still the truth. A memory layer has **no corpus behind it**. The record was the truth, other records were derived from it, its vector sits in a content-keyed cache, and a copy lives in whatever secondary store was added for query speed.

So the cascade has to reach each structure by name, and the list of structures exists nowhere except in the code that created them. On this course's corpus the address is in **three** places and none of them knows about the others.

Report the zeroes. A cascade that prints only what it removed is indistinguishable from one whose edges point nowhere — and this is the operation where that distinction is legally load-bearing.

Deletion cannot share a mechanism with supersession, which is designed never to destroy. The vector index has the same tension in miniature: it **tombstones** a retired belief and keeps its vector because an audit needs it, and deletion is exactly where that requirement inverts.

## Connections

<!-- graph:begin -->
**Taught in:** [Deletion That Actually Deletes](../curriculum/advanced/deletion-that-actually-deletes/index.md)

**Do not confuse with:** [Supersession](supersession.md)
<!-- graph:end -->
