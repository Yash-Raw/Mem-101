/* Per-viewer progress. Nothing here is a source of truth.
 *
 * The course has no way to tell a learner they are on lesson 7 of 84 or that
 * they finished lesson 6, and it has 84 of them -- which is most of why it
 * reads as overwhelming. This keeps a list of lesson ids in localStorage so
 * the strip can be ticked and the home page can say "continue".
 *
 * Rules it must not break: no figure the site displays is derived from this,
 * every access is wrapped because a private window throws on localStorage,
 * and the page must already be correct before this file runs -- the resume
 * banner is `display: none` until there is something true to put in it.
 */
(function () {
  "use strict";

  var KEY = "mem101:done";

  function read() {
    try {
      var raw = window.localStorage.getItem(KEY);
      var v = raw ? JSON.parse(raw) : [];
      return Object.prototype.toString.call(v) === "[object Array]" ? v : [];
    } catch (e) {
      return [];
    }
  }

  function write(ids) {
    try {
      window.localStorage.setItem(KEY, JSON.stringify(ids));
    } catch (e) {
      /* Storage disabled or full. The button still reflects this page. */
    }
  }

  /* A roadmap stop is finished when every lesson in its module is. Additive
   * only: the stop is already correct and clickable before this runs, so a
   * reader with no history or no JavaScript loses nothing. */
  function tickRoadmap(d, done) {
    var stops = document.querySelectorAll(".mem-road__stop[data-module]");
    if (!stops.length) { return; }
    var byModule = {};
    for (var i = 0; i < d.modules.length; i++) {
      byModule[d.modules[i].id] = d.modules[i].lessons;
    }
    for (var j = 0; j < stops.length; j++) {
      var ids = byModule[stops[j].getAttribute("data-module")] || [];
      var all = ids.length > 0;
      for (var k = 0; k < ids.length; k++) {
        if (done.indexOf(ids[k]) === -1) { all = false; break; }
      }
      if (all) { stops[j].className += " is-done"; }
    }
  }

  /* Home page: offer the next unfinished lesson. Hidden until it is true, so
   * there is no flash and no claim at all when scripts are off. */
  var resume = document.querySelector(".mem-resume");
  if (resume) {
    var done0 = read();
    if (done0.length) {
      var here = document.currentScript && document.currentScript.src;
      var data = new URL("../data/site.json", here);
      var base = new URL("../../", here);
      fetch(data).then(function (r) { return r.json(); }).then(function (d) {
        tickRoadmap(d, done0);
        var nextUp = null;
        for (var i = 0; i < d.lessons.length; i++) {
          if (done0.indexOf(d.lessons[i].id) === -1) { nextUp = d.lessons[i]; break; }
        }
        if (!nextUp) { return; }
        var a = resume.querySelector(".mem-resume__a");
        a.textContent = nextUp.title + " \u2014 lesson " + nextUp.position +
                        " of " + d.lessons.length;
        a.href = new URL(nextUp.path.replace(/index\.md$/, ""), base).href;
        resume.hidden = false;
        resume.className += " is-on";
      }).catch(function () { /* leave it hidden */ });
    }
  }

  var btn = document.querySelector(".mem-strip__done");
  if (!btn) { return; }

  var id = btn.getAttribute("data-lesson");
  var done = read();

  function paint() {
    var on = done.indexOf(id) !== -1;
    btn.setAttribute("aria-pressed", on ? "true" : "false");
    btn.textContent = on ? "Done" : "Mark done";
  }

  /* Revealed only now: with scripts off the button would do nothing, so it is
   * `hidden` in the template and unhidden here. */
  btn.hidden = false;
  paint();

  btn.addEventListener("click", function () {
    var i = done.indexOf(id);
    if (i === -1) { done.push(id); } else { done.splice(i, 1); }
    write(done);
    paint();
  });
})();
