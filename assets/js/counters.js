/* ==========================================================================
   Counting numbers
   --------------------------------------------------------------------------
   Counts the impact figures up when they scroll into view.

   The markup holds the final text, whatever shape it is - "120", "120+",
   "[120]" while it is still a placeholder. This finds the number inside,
   counts that, and leaves everything around it alone. If there is no number
   to find, the text is simply left as it is.
   ========================================================================== */

(function () {
  "use strict";

  var values = document.querySelectorAll("[data-count]");
  if (!values.length) return;

  var calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (calm || !("IntersectionObserver" in window)) return;   // final text already in the DOM

  function parse(text) {
    var match = text.match(/^(\D*?)(\d[\d,\s]*)(.*)$/s);
    if (!match) return null;
    var digits = match[2].replace(/[,\s]/g, "");
    if (!digits.length || digits.length > 9) return null;
    return { prefix: match[1], target: parseInt(digits, 10), suffix: match[3] };
  }

  function run(el) {
    var parts = parse(el.textContent.trim());
    if (!parts || parts.target === 0) return;

    var duration = 1500;
    var started = null;

    // Reserve the final width so the layout does not twitch while counting.
    el.style.minWidth = el.getBoundingClientRect().width + "px";

    function frame(now) {
      if (started === null) started = now;
      var progress = Math.min((now - started) / duration, 1);
      // Ease out, so it slows as it lands on the real figure.
      var eased = 1 - Math.pow(1 - progress, 3);
      var current = Math.round(parts.target * eased);

      el.textContent = parts.prefix + current.toLocaleString() + parts.suffix;

      if (progress < 1) {
        requestAnimationFrame(frame);
      } else {
        el.textContent = parts.prefix + parts.target.toLocaleString() + parts.suffix;
        el.style.minWidth = "";
      }
    }

    requestAnimationFrame(frame);
  }

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        run(entry.target);
      });
    },
    { threshold: 0.5 }
  );

  values.forEach(function (value) { observer.observe(value); });
})();
