/* ==========================================================================
   Navigation
   --------------------------------------------------------------------------
   The mobile menu, and the hairline that appears under the header once the
   page has scrolled. Both are enhancements: with JavaScript switched off the
   nav links are still in the page and still work.
   ========================================================================== */

(function () {
  "use strict";

  var toggle = document.querySelector(".nav__toggle");
  var panel = document.getElementById("nav-panel");
  var header = document.querySelector(".site-header");

  /* ---- Announce the current page --------------------------------------
     The highlight itself is pure CSS, driven by body[data-page], so it works
     without this. aria-current is what tells a screen reader which link is
     the page they are already on. */
  var page = document.body.getAttribute("data-page");
  if (page) {
    document.querySelectorAll('[data-nav="' + page + '"]').forEach(function (link) {
      link.setAttribute("aria-current", "page");
    });
  }

  /* ---- Mobile menu ----------------------------------------------------- */
  if (toggle && panel) {
    var label = toggle.querySelector(".nav__toggle-text");

    function setOpen(open) {
      toggle.setAttribute("aria-expanded", String(open));
      panel.classList.toggle("is-open", open);
      document.body.classList.toggle("nav-open", open);
      if (label) label.textContent = open ? "Close" : "Menu";

      if (open) {
        // Move focus into the panel so a keyboard user lands where they expect.
        var first = panel.querySelector("a, button");
        if (first) first.focus({ preventScroll: true });
      }
    }

    function isOpen() {
      return toggle.getAttribute("aria-expanded") === "true";
    }

    toggle.addEventListener("click", function () {
      setOpen(!isOpen());
    });

    // Escape closes and returns focus to the button that opened it.
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && isOpen()) {
        setOpen(false);
        toggle.focus();
      }
    });

    // Tapping a link closes the panel before the next page paints.
    panel.addEventListener("click", function (event) {
      if (event.target.closest("a")) setOpen(false);
    });

    // Keep focus inside the panel while it covers the page.
    panel.addEventListener("keydown", function (event) {
      if (event.key !== "Tab" || !isOpen()) return;

      var focusables = panel.querySelectorAll("a[href], button:not([disabled])");
      if (!focusables.length) return;

      var first = focusables[0];
      var last = focusables[focusables.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        toggle.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        toggle.focus();
      }
    });

    // Widening past the desktop breakpoint must not leave the body locked.
    var wide = window.matchMedia("(min-width: 62em)");
    var onChange = function (event) {
      if (event.matches && isOpen()) setOpen(false);
    };
    if (wide.addEventListener) wide.addEventListener("change", onChange);
    else if (wide.addListener) wide.addListener(onChange);
  }

  /* ---- Header shadow on scroll ----------------------------------------- */
  if (header) {
    var sentinel = document.createElement("div");
    sentinel.setAttribute("aria-hidden", "true");
    sentinel.style.cssText = "position:absolute;top:0;height:1px;width:1px;";
    document.body.prepend(sentinel);

    if ("IntersectionObserver" in window) {
      new IntersectionObserver(
        function (entries) {
          header.classList.toggle("is-stuck", !entries[0].isIntersecting);
        },
        { threshold: 0 }
      ).observe(sentinel);
    } else {
      window.addEventListener("scroll", function () {
        header.classList.toggle("is-stuck", window.scrollY > 4);
      }, { passive: true });
    }
  }
})();
