/* ==========================================================================
   Forms
   --------------------------------------------------------------------------
   Every form on the site works on day one, with or without a form service.

   - If data-endpoint has a URL (Formspree, Basin, Netlify Forms, anything
     that accepts a POST), the form is sent in the background and the visitor
     gets a thank-you without losing the page.
   - If it is empty, the form falls back to opening the visitor's email app
     with everything they typed already filled in. Nobody's enquiry is ever
     silently dropped.

   Validation is the browser's own, so the messages are the ones the visitor's
   device already uses, in their own language.
   ========================================================================== */

(function () {
  "use strict";

  var forms = document.querySelectorAll("form[data-form]");
  if (!forms.length) return;

  function say(status, state, message) {
    if (!status) return;
    status.setAttribute("data-state", state);
    status.textContent = message;
  }

  function readable(form) {
    // Turn the form into a plain-text summary for the email fallback.
    var lines = [];
    new FormData(form).forEach(function (value, key) {
      if (key.charAt(0) === "_" || !String(value).trim()) return;
      var field = form.elements[key];
      var label = key;
      if (field && field.id) {
        var tag = form.querySelector('label[for="' + field.id + '"]');
        if (tag) label = tag.textContent.trim().replace(/\s+/g, " ");
      }
      lines.push(label + ": " + value);
    });
    return lines.join("\n");
  }

  forms.forEach(function (form) {
    var status = form.querySelector(".form__status");
    var submit = form.querySelector('[type="submit"]');
    var endpoint = (form.getAttribute("data-endpoint") || "").trim();
    var mailto = (form.getAttribute("data-mailto") || "").trim();
    var subject = form.getAttribute("data-subject") || "Website enquiry";
    var thanks = form.getAttribute("data-thanks") ||
      "Thank you - we have got that and someone will come back to you soon.";

    form.addEventListener("submit", function (event) {
      // Let the browser show its own messages on an incomplete form.
      if (!form.checkValidity()) return;

      event.preventDefault();

      /* ---- No endpoint: hand over to the visitor's email app ----------- */
      if (!endpoint) {
        if (!mailto || mailto.indexOf("[") === 0) {
          say(status, "error",
            "This form is not connected yet. Please email us directly for now.");
          return;
        }
        var href = "mailto:" + mailto +
          "?subject=" + encodeURIComponent(subject) +
          "&body=" + encodeURIComponent(readable(form));
        window.location.href = href;
        say(status, "ok",
          "Your email app should be opening with your message ready to send.");
        return;
      }

      /* ---- Endpoint configured: post it quietly ------------------------ */
      say(status, "busy", "Sending...");
      if (submit) submit.disabled = true;

      fetch(endpoint, {
        method: "POST",
        headers: { Accept: "application/json" },
        body: new FormData(form)
      })
        .then(function (response) {
          if (!response.ok) throw new Error("Request failed: " + response.status);
          form.reset();
          say(status, "ok", thanks);
        })
        .catch(function () {
          say(status, "error",
            "Something went wrong sending that. Please try again, or email us at " +
            (mailto || "the address on our contact page") + ".");
        })
        .then(function () {
          if (submit) submit.disabled = false;
        });
    });
  });
})();
