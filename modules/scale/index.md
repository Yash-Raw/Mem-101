# Cost, Latency & Scale

*How does it survive time, scale, multiplicity, and scrutiny?*

Module 8 of 9 in **Time, Scale, Multiplicity, Trust** &middot; 4 lessons &middot; about 3.1 hours

**76. [The Write Path Dominates](../../curriculum/advanced/cost-model/index.md)** &middot; ~45 min

Count the calls: the read path makes none, and the write path makes two per turn.

**77. [The Latency Budget](../../curriculum/advanced/latency-budget/index.md)** &middot; ~45 min

Half the per-turn cost blocks -- and the other half is a model call in a stage called deferrable.

**78. [Caching, Batching, Routing](../../curriculum/advanced/caching-batching-routing/index.md)** &middot; ~45 min

Two of six tactics do not apply, and routing has two targets rather than one.

**79. [Scaling the Store](../../curriculum/advanced/scaling-the-store/index.md)** &middot; ~50 min

Replicate and measure -- retrieval grows linearly, consolidation grows 104x.

[Start with The Write Path Dominates &rarr;](../../curriculum/advanced/cost-model/index.md)
