/* Concept atlas -- the lesson<->concept graph, one neighbourhood at a time.
 *
 * The prerequisite graph is not drawn here on purpose: every lesson has at most
 * one prerequisite and unlocks at most one other, so it is a single chain
 * identical to reading order, and drawing it would teach nothing. The graph
 * that branches is lesson<->concept, and that is what this file draws.
 *
 * Every count, title and relationship comes from assets/data/site.json. There
 * is no number in this file that describes the course.
 *
 * Paths are derived from this script's own URL, never root-absolute: the site
 * is served from a subpath in production and from / under `mkdocs serve`.
 *
 * SVG colour is set through `style`, never through a presentation attribute.
 * `fill="var(--mem-accent)"` does not resolve in any engine -- the property
 * falls back to its initial value, so edges vanish and nodes render black.
 */
(function () {
  "use strict";

  var HERE = document.currentScript.src;          /* .../assets/js/atlas.js */
  var DATA = new URL("../data/site.json", HERE);
  var BASE = new URL("../../", HERE);             /* site root */
  var SVGNS = "http://www.w3.org/2000/svg";

  /* Amber is the retrieve stage everywhere else on this site, and a concept's
   * stage shows in the detail panel below -- so contrast edges are neutral
   * rather than amber, and stay told apart by dash and width.
   *
   * The one place the relation vocabulary is defined. The legend in
   * docs/atlas.md is hand-written and mirrors this table: each relation is a
   * dash pattern AND a stroke width AND a colour, so none of it is carried by
   * colour alone. */
  /* `key` is the same relation named for the detail panel, where .mem-kv__k is
   * a fixed 5.4rem: the graph's heading would wrap in it. */
  var REL = {
    taught:   { head: "TAUGHT HERE",         key: "TAUGHT HERE",   dash: null,      w: 2.2, colour: "var(--mem-accent)" },
    used:     { head: "USED HERE",           key: "USED HERE",     dash: "6 4",     w: 1.4, colour: "var(--mem-faint)" },
    contrast: { head: "DO NOT CONFUSE WITH", key: "CONFUSED WITH", dash: "1.5 3.5", w: 1.1, colour: "var(--mem-fainter)" }
  };
  /* Level is a glyph as well as a hue, the same pair .mem-lv uses in CSS. */
  var GLYPH = { beginner: "●", intermediate: "◒", advanced: "○", concept: "◇" };
  var LEVEL = { beginner: "var(--mem-l1)", intermediate: "var(--mem-l2)", advanced: "var(--mem-l3)" };

  var PILL_FONT = "font-family: var(--mem-serif); font-size: 17px; font-weight: 600";
  var ROW_FONT = "font-family: var(--mem-serif); font-size: 14px";
  var GLYPH_FONT = "font-family: var(--mem-mono); font-size: 12px";
  /* Mirrors .mem-lbl, which the block headings wear -- measuring them needs
   * the letter-spacing too, or a heading overruns the space reserved for it. */
  var LBL_FONT = "font-family: var(--mem-mono); font-size: 11px; letter-spacing: 0.09em";

  var ROW = 26, HEAD = 22, GAP = 16, PILL_H = 36, ARM = 66, LABEL_PAD = 13, PAD = 10;
  var BILATERAL_MIN = 600, LIST_MAX = 14;

  var state = { concepts: [], byId: {}, lessons: {}, hubs: [], stats: null,
                focus: null, query: "", width: 0 };

  /* ---- tiny DOM helpers ---------------------------------------------- */

  function attr(node, a) {
    for (var k in a) { if (a[k] !== null && a[k] !== undefined) node.setAttribute(k, a[k]); }
    return node;
  }
  function h(tag, a, kids) {
    var n = attr(document.createElement(tag), a || {});
    (kids || []).forEach(function (k) {
      n.appendChild(typeof k === "string" ? document.createTextNode(k) : k);
    });
    return n;
  }
  function svg(tag, a, kids) {
    var n = attr(document.createElementNS(SVGNS, tag), a || {});
    (kids || []).forEach(function (k) {
      n.appendChild(typeof k === "string" ? document.createTextNode(k) : k);
    });
    return n;
  }
  function clear(node) { while (node.firstChild) { node.removeChild(node.firstChild); } }
  function by(id) { return document.getElementById(id); }

  /* ---- URLs, derived from the data ------------------------------------ */

  function conceptHref(id) { return new URL("concepts/" + id + "/", BASE).href; }
  function lessonHref(l) {
    /* curriculum/<level>/<id>/index.md -> curriculum/<level>/<id>/ */
    return new URL(l.path.replace(/index\.md$/, ""), BASE).href;
  }

  /* ---- the focused neighbourhood -------------------------------------- */

  function lessonItem(id) {
    var l = state.lessons[id];
    return { kind: "lesson", id: id, title: l.title, level: l.level,
             glyph: GLYPH[l.level], colour: LEVEL[l.level], href: lessonHref(l) };
  }
  function conceptItem(id) {
    var c = state.byId[id];
    /* Three contrasts_with edges name two ids with no concept page. Show
     * them as they are stored -- unlinked, raw id -- rather than inventing a
     * title or hiding an edge the data claims exists. */
    return { kind: "concept", id: id, title: c ? c.title : id, glyph: GLYPH.concept,
             colour: c ? "var(--mem-alt)" : "var(--mem-muted)",
             href: c ? conceptHref(id) : null, focusable: !!c, missing: !c };
  }
  function groupsFor(c) {
    var g = [];
    if (c.taught_in.length) { g.push({ rel: "taught", side: 1, items: c.taught_in.map(lessonItem) }); }
    if (c.used_in.length) { g.push({ rel: "used", side: 1, items: c.used_in.map(lessonItem) }); }
    if (c.contrasts_with.length) { g.push({ rel: "contrast", side: -1, items: c.contrasts_with.map(conceptItem) }); }
    return g;
  }

  /* ---- text measurement ------------------------------------------------
   * A hidden <text> kept as a sibling of the content group -- inside it, its
   * geometry would be counted by getBBox() and inflate the viewBox. */

  var ruler = null;
  function measure(str, font) {
    ruler.setAttribute("style", "visibility: hidden; " + font);
    ruler.textContent = str;
    return ruler.getComputedTextLength();
  }
  function fit(str, budget, font) {
    if (measure(str, font) <= budget) { return str; }
    var lo = 0, hi = str.length, mid;
    while (lo < hi) {
      mid = Math.ceil((lo + hi) / 2);
      if (measure(str.slice(0, mid) + "…", font) <= budget) { lo = mid; } else { hi = mid - 1; }
    }
    return str.slice(0, lo).replace(/[\s–—-]+$/, "") + "…";
  }

  /* ---- layout ----------------------------------------------------------
   * Two arrangements over one row list. Both fill in x / y / labelX / anchor /
   * edge on every item, so drawing is the same code either way.
   *
   * bilateral (>= BILATERAL_MIN of measured width): the concept sits in the
   * middle; lessons fan right (taught above used), contrasted concepts fan
   * left. Each side is a stack of blocks, centred on the pill's own centre.
   *
   * stacked (narrower): the same rows in one column under the pill, joined by
   * elbows off a per-group rail. Labels get the full width, so a phone gets a
   * legible list with the dash vocabulary intact rather than a pinch-zoom
   * canvas. */

  function blockHeight(gs) {
    var t = 0;
    gs.forEach(function (g) { t += HEAD + g.items.length * ROW; });
    return t + GAP * Math.max(0, gs.length - 1);
  }

  function placeBilateral(groups, width, pillW, armCap) {
    var half = width / 2;
    var armX = Math.min(Math.max(pillW / 2 + ARM, 120), armCap);
    var budget = half - armX - LABEL_PAD - 8;
    [1, -1].forEach(function (side) {
      var gs = groups.filter(function (g) { return g.side === side; });
      var y = -blockHeight(gs) / 2;
      gs.forEach(function (g) {
        g.headX = side * (armX + LABEL_PAD);
        g.headY = y + 13;
        g.anchor = side > 0 ? "start" : "end";
        y += HEAD;
        g.items.forEach(function (it) {
          it.x = side * armX;
          it.y = y + ROW / 2;
          it.labelX = side * (armX + LABEL_PAD);
          it.anchor = g.anchor;
          it.budget = budget;
          var x0 = side * (pillW / 2), x1 = side * (armX - 9);
          it.edge = "M " + x0 + ",0 C " + (x0 + side * 34) + ",0 " +
                    (x1 - side * 40) + "," + it.y + " " + x1 + "," + it.y;
          y += ROW;
        });
        y += GAP;
      });
    });
    return { x: -pillW / 2, y: -PILL_H / 2, cx: 0, cy: 0 };
  }

  function placeStacked(groups, width, pillW) {
    var armX = 46, labelX = 60, budget = Math.max(60, width - labelX - 8);
    var y = PILL_H + 18;
    groups.forEach(function (g, gi) {
      var rail = 9 + gi * 5;
      g.headX = labelX;
      g.headY = y + 13;
      g.anchor = "start";
      y += HEAD;
      g.items.forEach(function (it) {
        it.x = armX;
        it.y = y + ROW / 2;
        it.labelX = labelX;
        it.anchor = "start";
        it.budget = budget;
        it.edge = "M " + rail + "," + (PILL_H + 4) + " L " + rail + "," + (it.y - 9) +
                  " Q " + rail + "," + it.y + " " + (rail + 11) + "," + it.y +
                  " L " + (armX - 9) + "," + it.y;
        y += ROW;
      });
      y += GAP;
    });
    return { x: 0, y: 0, cx: pillW / 2, cy: PILL_H / 2 };
  }

  /* ---- the graph ------------------------------------------------------- */

  function drawGraph() {
    var host = by("mem-atlas-graph");
    var c = state.byId[state.focus];
    if (!host || !c) { return; }

    host.setAttribute("class", "mem-atlas mem-wide");   /* also clears is-focused */
    clear(host);

    var root = svg("svg", { role: "group", "aria-label":
      c.title + ": the lessons that teach and use it, and the concepts it is confused with." });
    host.appendChild(root);

    var width = Math.round(root.getBoundingClientRect().width || host.getBoundingClientRect().width);
    if (width < 40) { return; }          /* not laid out yet; the observer will call back */
    state.width = width;

    ruler = svg("text", { style: "visibility: hidden" });
    root.appendChild(ruler);
    var content = svg("g", {});
    root.appendChild(content);

    var groups = groupsFor(c);
    var pillW = Math.ceil(measure(c.title, PILL_FONT)) + 28;

    /* Block headings are the legend's own words and are never abbreviated, so
     * they set how far the arms may reach: past this the widest heading runs
     * off the canvas. A pill that leaves no room for them takes the stacked
     * arrangement instead of a squeezed one. */
    var headW = 0;
    groups.forEach(function (g) {
      headW = Math.max(headW, measure(REL[g.rel].head, LBL_FONT));
    });
    var armCap = width / 2 - 8 - LABEL_PAD - headW;
    var pill = (width >= BILATERAL_MIN && armCap >= pillW / 2 + 24)
      ? placeBilateral(groups, width, pillW, armCap)
      : placeStacked(groups, width, pillW);

    var nodes = [];
    var edges = svg("g", {});
    var marks = svg("g", {});
    content.appendChild(edges);
    content.appendChild(marks);

    groups.forEach(function (g) {
      var rel = REL[g.rel];
      marks.appendChild(svg("text", {
        "class": "mem-lbl", x: g.headX, y: g.headY, "text-anchor": g.anchor,
        style: "fill: var(--mem-muted)"
      }, [rel.head]));

      g.items.forEach(function (it) {
        var edge = svg("path", {
          "class": "mem-atlas__edge", d: it.edge, "stroke-width": rel.w,
          "stroke-dasharray": rel.dash,
          style: "fill: none; stroke: " + rel.colour
        });
        edges.appendChild(edge);

        var inner = [
          svg("text", { x: it.x, y: it.y, "text-anchor": "middle",
            "dominant-baseline": "central", style: GLYPH_FONT + "; fill: " + it.colour },
            [it.glyph]),
          svg("text", { x: it.labelX, y: it.y, "text-anchor": it.anchor,
            "dominant-baseline": "central", style: ROW_FONT + "; fill: var(--mem-alt)" },
            [fit(it.title, it.budget, ROW_FONT)]),
          svg("title", {}, [it.kind === "lesson"
            ? it.title + " — open the lesson"
            : (it.missing ? it.title + " — no concept page" : it.title + " — focus this concept")])
        ];

        var node;
        if (it.href && it.kind === "lesson") {
          node = svg("a", { "class": "mem-atlas__node", href: it.href }, inner);
        } else if (it.focusable) {
          node = svg("g", { "class": "mem-atlas__node", role: "button", tabindex: "0" }, inner);
          node.addEventListener("click", function () { focus(it.id); });
          node.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === " ") { e.preventDefault(); focus(it.id); }
          });
        } else {
          node = svg("g", { "class": "mem-atlas__node", style: "cursor: default" }, inner);
        }
        marks.appendChild(node);
        nodes.push({ node: node, edge: edge });
      });
    });

    /* The pill is drawn last so the edges run behind it, and it is filled --
     * that is what keeps a fan of edges from crossing the title. */
    var centre = svg("a", { "class": "mem-atlas__node", href: conceptHref(c.id) }, [
      svg("rect", { x: pill.x, y: pill.y, width: pillW, height: PILL_H, rx: 9,
        "stroke-width": 1.6,
        style: "fill: var(--mem-surface); stroke: var(--mem-accent)" }),
      svg("text", { x: pill.cx, y: pill.cy, "text-anchor": "middle",
        "dominant-baseline": "central", style: PILL_FONT + "; fill: var(--mem-fg)" },
        [c.title]),
      svg("title", {}, [c.title + " — open the concept page"])
    ]);
    content.appendChild(centre);

    nodes.forEach(function (n) {
      function on() {
        host.classList.add("is-focused");
        n.node.classList.add("is-lit");
        n.edge.classList.add("is-lit");
        centre.classList.add("is-lit");
      }
      function off() {
        host.classList.remove("is-focused");
        n.node.classList.remove("is-lit");
        n.edge.classList.remove("is-lit");
        centre.classList.remove("is-lit");
      }
      n.node.addEventListener("mouseenter", on);
      n.node.addEventListener("mouseleave", off);
      n.node.addEventListener("focusin", on);
      n.node.addEventListener("focusout", off);
    });

    /* The viewBox is the measured bounding box of what was actually drawn --
     * text, glyphs, curves and all -- not a guessed canvas. An empty side or a
     * long title therefore recentres the drawing instead of skewing it. */
    root.removeChild(ruler);
    ruler = null;
    var box = content.getBBox();
    root.setAttribute("viewBox", [
      (box.x - PAD).toFixed(1), (box.y - PAD).toFixed(1),
      (box.width + PAD * 2).toFixed(1), (box.height + PAD * 2).toFixed(1)
    ].join(" "));
  }

  /* ---- detail panel ----------------------------------------------------- */

  function lessonLine(id) {
    var l = state.lessons[id];
    return h("div", { style: "margin-bottom: 3px" }, [
      h("span", { "class": "mem-lv", "data-level": l.level }, [
        h("a", { href: lessonHref(l) }, [l.title])
      ])
    ]);
  }
  function conceptChip(id) {
    var c = state.byId[id];
    if (!c) { return h("span", { "class": "mem-chip", style: "cursor: default" }, [id]); }
    var chip = h("button", { type: "button", "class": "mem-chip" }, [c.title]);
    chip.addEventListener("click", function () { focus(id); });
    return chip;
  }
  function kv(key, value) {
    return h("div", { "class": "mem-kv" }, [
      h("span", { "class": "mem-kv__k" }, [key]),
      h("div", { "class": "mem-kv__v" }, [value])
    ]);
  }
  function none() { return h("span", { "class": "mem-count" }, ["none"]); }

  function conceptPanel(c) {
    var taught = c.taught_in.length
      ? h("div", {}, c.taught_in.map(lessonLine)) : none();
    var used = c.used_in.length
      ? h("div", {}, c.used_in.map(lessonLine)) : none();
    var contrast = c.contrasts_with.length
      ? h("div", { style: "display: flex; flex-wrap: wrap; gap: 5px" },
          c.contrasts_with.map(conceptChip))
      : none();
    return h("div", { "class": "mem-panel", style: "padding: 0.95rem 1.1rem" }, [
      h("div", { "class": "mem-lbl" }, ["FOCUSED CONCEPT"]),
      h("div", { "class": "mem-lesson__t" }, [h("a", { href: conceptHref(c.id) }, [c.title])]),
      h("div", { style: "margin-bottom: 0.8rem" }, [
        h("span", { "class": "mem-stage", "data-stage": c.stage }, [c.stage]),
        h("span", { "class": "mem-count" }, [
          "  ·  " + c.touches + (c.touches === 1 ? " lesson touches it" : " lessons touch it")
        ])
      ]),
      kv(REL.taught.key, taught),
      kv(REL.used.key, used),
      kv(REL.contrast.key, contrast)
    ]);
  }

  /* ---- picker ----------------------------------------------------------- */

  function matches() {
    var q = state.query.trim().toLowerCase();
    if (!q) { return state.hubs.map(function (x) { return state.byId[x.id]; }); }
    return state.concepts.filter(function (c) {
      return c.title.toLowerCase().indexOf(q) >= 0 || c.id.indexOf(q) >= 0;
    }).sort(function (a, b) {
      return b.touches - a.touches || a.title.localeCompare(b.title);
    });
  }

  function rankRow(c, top) {
    var max = state.hubs.length ? state.hubs[0].touches : c.touches;
    var style = "background: none; border: 0; padding: 3px 0; width: 100%;" +
      " text-align: left; cursor: pointer; color: inherit; font-family: inherit" +
      (c.id === state.focus ? "; font-weight: 600" : "");
    var row = h("button", {
      type: "button", "class": "mem-rank" + (top ? " mem-rank--top" : ""),
      style: style, "aria-current": c.id === state.focus ? "true" : null
    }, [
      h("span", { style: "overflow: hidden; text-overflow: ellipsis; white-space: nowrap" },
        [c.title]),
      h("span", { "class": "mem-rank__bar",
        style: "width: " + Math.max(6, Math.round(100 * c.touches / max)) + "%" }),
      h("span", { "class": "mem-rank__n" }, [String(c.touches)])
    ]);
    row.addEventListener("click", function () { focus(c.id); });
    return row;
  }

  function totalsLine() {
    var s = state.stats;
    return h("p", { "class": "mem-count", style: "margin: 0.9rem 0 0" }, [
      s.concepts + " concepts · " + s.graph.lesson_concept_edges +
      " lesson↔concept links · " + s.hubs_at_threshold + " touched by " +
      s.hub_threshold + " or more lessons · " + s.concepts_touched_once + " touched once"
    ]);
  }

  function pickerPanel() {
    var list = matches();
    var shown = list.slice(0, LIST_MAX);
    var panel = h("div", { "class": "mem-panel", style: "padding: 0.95rem 1.1rem" }, [
      h("div", { "class": "mem-lbl", style: "margin-bottom: 0.6rem" },
        [state.query.trim() ? "MATCHING CONCEPTS" : "MOST-TOUCHED CONCEPTS"])
    ]);
    if (!shown.length) {
      panel.appendChild(h("p", { "class": "mem-empty" }, ["No concept matches that."]));
    }
    shown.forEach(function (c, i) { panel.appendChild(rankRow(c, i === 0)); });
    panel.appendChild(totalsLine());

    var count = by("mem-atlas-count");
    if (count) {
      clear(count);
      count.appendChild(document.createTextNode(
        shown.length === list.length
          ? list.length + " of " + state.concepts.length + " concepts"
          : "showing " + shown.length + " of " + list.length + " matches"));
    }
    return panel;
  }

  function drawDetail() {
    var host = by("mem-atlas-detail");
    if (!host) { return; }
    clear(host);
    host.appendChild(conceptPanel(state.byId[state.focus]));
    host.appendChild(pickerPanel());
  }

  /* ---- wiring ----------------------------------------------------------- */

  /* `quiet` is the first draw: the URL is only rewritten once the reader has
   * actually chosen something, so landing on the page leaves the address bar
   * alone and a shared link still opens on the concept it names. */
  function focus(id, quiet) {
    if (!state.byId[id]) { return; }
    state.focus = id;
    if (!quiet && window.history && history.replaceState) {
      history.replaceState(null, "", "#" + id);
    }
    drawGraph();
    drawDetail();
  }

  function boot(data) {
    state.concepts = data.concepts;
    state.hubs = data.hubs;
    state.stats = data.stats;
    data.concepts.forEach(function (c) { state.byId[c.id] = c; });
    data.lessons.forEach(function (l) { state.lessons[l.id] = l; });

    var q = by("mem-atlas-q");
    if (q) {
      q.addEventListener("input", function () { state.query = q.value; drawDetail(); });
      q.addEventListener("keydown", function (e) {
        if (e.key !== "Enter") { return; }
        e.preventDefault();
        var first = matches()[0];
        if (first) { focus(first.id); }
      });
    }

    var start = decodeURIComponent((location.hash || "").slice(1));
    focus(state.byId[start] ? start : data.hubs[0].id, true);

    var host = by("mem-atlas-graph");
    function onResize() {
      var w = Math.round(host.getBoundingClientRect().width);
      if (Math.abs(w - state.width) > 2) { drawGraph(); }
    }
    if (host && window.ResizeObserver) { new ResizeObserver(onResize).observe(host); }
    else if (host) { window.addEventListener("resize", onResize); }
    /* Labels are measured, so a late webfont would invalidate every truncation. */
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () { drawGraph(); });
    }
  }

  function fail(err) {
    var host = by("mem-atlas-graph");
    if (!host) { return; }
    clear(host);
    host.appendChild(h("p", { "class": "mem-empty" },
      ["The graph data did not load (" + err + ")."]));
  }

  function run() {
    fetch(DATA.href, { credentials: "same-origin" })
      .then(function (r) {
        if (!r.ok) { throw new Error(r.status + " " + r.statusText); }
        return r.json();
      })
      .then(boot)
      .catch(fail);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
}());
