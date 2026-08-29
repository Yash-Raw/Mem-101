# Concept Atlas

The course reads in a straight line: every lesson has at most one prerequisite
and unlocks at most one other, so the prerequisite graph is the reading order
drawn a second time. The structure that actually branches sits underneath it —
which lesson **teaches** a concept, which lessons later **use** it, and which
concept it keeps getting confused with — and that is what this draws.

Pick a concept and it moves to the middle. Hover a node to drop everything it
does not touch.

<!-- The three swatches mirror the REL table in assets/js/atlas.js: each
     relation is a dash pattern AND a stroke width AND a colour, so none of the
     three is told apart by colour alone. Change one, change both. -->
<div class="mem-legend mem-wide">
  <span class="mem-legend__i"><svg width="36" height="10" aria-hidden="true"><line x1="1" y1="5" x2="35" y2="5" stroke-width="2.2" style="stroke: var(--mem-accent)"></line></svg><span><b>Solid</b> — taught here</span></span>
  <span class="mem-legend__i"><svg width="36" height="10" aria-hidden="true"><line x1="1" y1="5" x2="35" y2="5" stroke-width="1.4" stroke-dasharray="6 4" style="stroke: var(--mem-faint)"></line></svg><span><b>Dashed</b> — used here</span></span>
  <span class="mem-legend__i"><svg width="36" height="10" aria-hidden="true"><line x1="1" y1="5" x2="35" y2="5" stroke-width="1.1" stroke-dasharray="1.5 3.5" style="stroke: var(--mem-fainter)"></line></svg><span><b>Dotted</b> — do not confuse with</span></span>
</div>
<div class="mem-toolbar mem-wide">
  <span class="mem-lbl">Concept</span>
  <input id="mem-atlas-q" class="mem-search" type="search" autocomplete="off" placeholder="filter concepts…" aria-label="Filter concepts">
  <span id="mem-atlas-count" class="mem-count"></span>
</div>
<div id="mem-atlas-graph" class="mem-atlas mem-wide"><p class="mem-empty">Loading the graph…</p></div>
<div id="mem-atlas-detail" class="mem-detail mem-wide"></div>

<script src="../assets/js/atlas.js"></script>
