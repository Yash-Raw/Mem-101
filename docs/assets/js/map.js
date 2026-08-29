/* The course map.
 *
 * Every figure this page shows -- how many lessons, how many hours, the level
 * titles and the questions they ask, the pipeline stage names, every lesson
 * title and objective -- is read from assets/data/site.json at runtime.
 * Nothing is typed in here. A number typed into a page is a number that goes
 * stale without anything failing, and this repository has spent enough time
 * chasing those.
 *
 * Paths are derived from this script's own URL, never from the site root. The
 * published site is served from a subpath, so fetch("/assets/data/site.json")
 * resolves to the domain root: it works under a root-served `mkdocs serve` and
 * 404s in production, which is the worst order in which to find out.
 *
 * The DOM is built with createElement and textContent throughout, so titles
 * containing quotes, ampersands or angle brackets are data rather than markup.
 */
(function () {
  "use strict";

  /* currentScript is null if the theme ever re-injects body scripts on a
   * client-side navigation, so fall back to finding this file by name. */
  var SELF = document.currentScript || document.querySelector('script[src$="/map.js"]');
  var mount = document.getElementById("mem-map");
  if (!mount) return;
  if (!SELF) {
    mount.textContent = "The lesson list could not work out where its data lives.";
    return;
  }

  var HERE = SELF.src;                              // .../assets/js/map.js
  var DATA = new URL("../data/site.json", HERE);    // .../assets/data/site.json
  var BASE = new URL("../../", HERE);               // the site root

  /* No filter on an axis. Empty string so it is falsy and never a real id. */
  var ALL = "";

  var course = null;   /* site.json, once it has arrived */
  var state = { level: ALL, stage: ALL, q: "", terms: [] };
  var chips = [];
  var countEl = null;
  var resultsEl = null;

  /* ---- little helpers ---------------------------------------------------- */

  function el(tag, attrs, kids) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (key) {
        var value = attrs[key];
        if (value === null || value === undefined) return;
        if (key === "text") node.textContent = value;
        else node.setAttribute(key, value);
      });
    }
    (kids || []).forEach(function (kid) { node.appendChild(kid); });
    return node;
  }

  /* "curriculum/<level>/<id>/index.md" -> "<site root>curriculum/<level>/<id>/" */
  function lessonHref(path) {
    return new URL(String(path).replace(/index\.md$/, ""), BASE).href;
  }

  function minutesOf(lessons) {
    return lessons.reduce(function (sum, lesson) { return sum + lesson.minutes; }, 0);
  }

  /* Computed rather than read from stats.levels, because it has to stay right
   * for a filtered subset too. Checked against stats for the unfiltered case. */
  function tally(lessons) {
    var n = lessons.length;
    return n + (n === 1 ? " lesson" : " lessons") +
      " · " + (minutesOf(lessons) / 60).toFixed(1) + " h";
  }

  /* ---- filtering ---------------------------------------------------------- */

  function matches(lesson) {
    if (state.level && lesson.level !== state.level) return false;
    if (state.stage && lesson.stage !== state.stage) return false;
    if (!state.terms.length) return true;
    var hay = (lesson.title + " " + lesson.objective).toLowerCase();
    return state.terms.every(function (term) { return hay.indexOf(term) !== -1; });
  }

  function activeFilters() {
    var bits = [];
    if (state.q.trim()) bits.push("“" + state.q.trim() + "”");
    if (state.stage) bits.push("stage " + state.stage);
    if (state.level) bits.push("level " + state.level);
    return bits.join(" · ");
  }

  /* ---- rendering ---------------------------------------------------------- */

  function chip(axis, value, label, cls, dataKey, spoken) {
    var attrs = {
      type: "button",
      "class": cls,
      "aria-pressed": "false",
      "aria-label": spoken,
      text: label
    };
    if (dataKey && value) attrs[dataKey] = value;
    var button = el("button", attrs);
    button.addEventListener("click", function () {
      /* Clicking the chip that is already on turns it off, which is what a
       * pressed toggle should do -- the "all" chip is a shortcut, not the
       * only way back. */
      state[axis] = state[axis] === value ? ALL : value;
      render();
    });
    chips.push({ axis: axis, value: value, node: button });
    return button;
  }

  function toolbar(data) {
    var bar = el("div", { "class": "mem-toolbar" });

    bar.appendChild(el("span", { "class": "mem-lbl", text: "level" }));
    bar.appendChild(chip("level", ALL, "all", "mem-chip", null, "All levels"));
    data.stats.levels.forEach(function (level) {
      bar.appendChild(chip(
        "level", level.id, level.id, "mem-chip mem-lv", "data-level",
        "Level: " + level.title
      ));
    });

    bar.appendChild(el("span", { "class": "mem-toolbar__sep", "aria-hidden": "true" }));

    bar.appendChild(el("span", { "class": "mem-lbl", text: "stage" }));
    bar.appendChild(chip("stage", ALL, "all", "mem-chip", null, "All stages"));
    data.stats.stages.forEach(function (stage) {
      bar.appendChild(chip(
        "stage", stage.id, stage.id, "mem-chip mem-stage", "data-stage",
        "Pipeline stage: " + stage.id
      ));
    });

    var search = el("input", {
      type: "search",
      "class": "mem-search",
      id: "mem-map-search",
      placeholder: "search titles and objectives",
      "aria-label": "Search lessons by title and objective",
      autocomplete: "off",
      autocapitalize: "off",
      spellcheck: "false"
    });
    search.addEventListener("input", function () {
      state.q = search.value;
      state.terms = search.value.toLowerCase().split(/\s+/).filter(Boolean);
      render();
    });
    search.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") return;
      search.value = "";
      state.q = "";
      state.terms = [];
      render();
    });
    bar.appendChild(search);

    countEl = el("span", { "class": "mem-count", role: "status" });
    bar.appendChild(countEl);

    return bar;
  }

  function card(lesson) {
    return el("a", { "class": "mem-card", href: lessonHref(lesson.path) }, [
      el("div", { "class": "mem-lesson__top" }, [
        el("span", { "class": "mem-stage", "data-stage": lesson.stage, text: lesson.stage }),
        el("span", { "class": "mem-lesson__min", text: lesson.minutes + " min" })
      ]),
      el("div", { "class": "mem-lesson__t", text: lesson.title }),
      el("div", { "class": "mem-lesson__o", text: lesson.objective })
    ]);
  }

  function levelSection(level, lessons) {
    var headingId = "mem-map-level-" + level.id;
    var head = el("div", { "class": "mem-level-head" }, [
      el("span", { "class": "mem-lv", "data-level": level.id, text: level.id }),
      el("span", { "class": "mem-level-head__t", id: headingId, text: level.title }),
      el("span", { "class": "mem-level-head__q", text: level.question }),
      el("span", { "class": "mem-level-head__n", text: tally(lessons) })
    ]);
    /* The grid sizes itself with container queries, so it needs the wrapper
     * that establishes the container -- Material's content width moves with
     * the nav, not with the window. */
    var grid = el("div", { "class": "mem-grid" }, lessons.map(card));
    return el("section", { "aria-labelledby": headingId }, [
      head,
      el("div", { "class": "mem-grid-wrap" }, [grid])
    ]);
  }

  function render() {
    chips.forEach(function (entry) {
      entry.node.setAttribute("aria-pressed", state[entry.axis] === entry.value ? "true" : "false");
    });

    var hits = course.lessons.filter(matches);
    countEl.textContent = tally(hits);

    resultsEl.textContent = "";
    if (!hits.length) {
      var filters = activeFilters();
      resultsEl.appendChild(el("p", {
        "class": "mem-empty",
        text: "Nothing matches " + (filters || "that combination") +
          ". Clear the search, or pick another stage."
      }));
      return;
    }

    course.stats.levels.forEach(function (level) {
      var inLevel = hits.filter(function (lesson) { return lesson.level === level.id; });
      if (!inLevel.length) return;
      inLevel.sort(function (a, b) { return a.order - b.order; });
      resultsEl.appendChild(levelSection(level, inLevel));
    });
  }

  function fail(reason) {
    mount.textContent = "";
    var link = el("a", { href: new URL("SYLLABUS/", BASE).href, text: "syllabus" });
    var note = el("p", { "class": "mem-empty" }, [
      document.createTextNode("The lesson list could not load (" + reason + "). " +
        "The same lessons, in the same order, are in the "),
      link,
      document.createTextNode(".")
    ]);
    mount.appendChild(note);
  }

  function boot(data) {
    course = data;
    mount.textContent = "";
    mount.appendChild(toolbar(data));
    resultsEl = el("div");
    mount.appendChild(resultsEl);
    render();
  }

  fetch(DATA.href, { credentials: "same-origin" })
    .then(function (response) {
      if (!response.ok) throw new Error("HTTP " + response.status);
      return response.json();
    })
    .then(function (data) {
      if (!data || !Array.isArray(data.lessons) || !data.stats ||
          !Array.isArray(data.stats.levels) || !Array.isArray(data.stats.stages)) {
        throw new Error("unexpected data shape");
      }
      boot(data);
    })
    .catch(function (error) {
      fail(error && error.message ? error.message : String(error));
    });
}());
