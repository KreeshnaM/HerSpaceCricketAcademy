/* ==========================================================================
   Scroll reveal
   --------------------------------------------------------------------------
   Adds .is-in to anything marked [data-reveal] once it comes into view, which
   lets the CSS slide it up into place. Items inside the same [data-reveal-group]
   are staggered so a row arrives as a run rather than all at once.

   The class only ever REMOVES a starting offset, so if this script never runs
   the page still looks right - see the .no-js rule in base.css.
   ========================================================================== */

(function () {
  "use strict";

  var items = document.querySelectorAll("[data-reveal]");
  if (!items.length) return;

  var calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (calm || !("IntersectionObserver" in window)) {
    items.forEach(function (item) { item.classList.add("is-in"); });
    return;
  }

  // Stagger within a group: 0ms, 90ms, 180ms... capped so a long list never
  // leaves the last item waiting.
  document.querySelectorAll("[data-reveal-group]").forEach(function (group) {
    var step = parseInt(group.getAttribute("data-reveal-group"), 10) || 90;
    group.querySelectorAll("[data-reveal]").forEach(function (child, index) {
      child.style.setProperty("--reveal-delay", Math.min(index * step, 540) + "ms");
    });
  });

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in");
        observer.unobserve(entry.target);   // reveal once, then forget it
      });
    },
    { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
  );

  items.forEach(function (item) { observer.observe(item); });

  /* Decorative ball-trajectory arcs draw themselves in the same way. */
  var arcs = document.querySelectorAll(".trajectory--draw");
  if (arcs.length) {
    var arcObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-in");
          arcObserver.unobserve(entry.target);
        });
      },
      { threshold: 0.25 }
    );
    arcs.forEach(function (arc) { arcObserver.observe(arc); });
  }
})();
