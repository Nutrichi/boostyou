/* Boostyou.ai — newsletter CTA component.
   Usage: <div class="newsletter-cta" data-heading="..." data-sub="..."></div>
   cta.js injects the form into every .newsletter-cta on the page.

   NEWSLETTER_ENDPOINT is the Google Apps Script web-app /exec URL
   (script source: tools/newsletter-apps-script.gs); it appends each
   address to the "Boostyou subscribers" Google Sheet. While empty,
   submissions are validated and answered with a thank-you but stored
   nowhere. The body is sent as text/plain because Apps Script cannot
   answer CORS preflight requests — text/plain keeps the POST a "simple
   request" so no preflight happens. */

var NEWSLETTER_ENDPOINT = 'https://script.google.com/macros/s/AKfycbyQTtiDYBlOcWf9hSZs6kj2fbc8tR0JxFAvl0Y0lEXVRJY8Qk1kKPhdlm_qbOFhAzaA0w/exec';

(function () {
  var DEFAULT_HEADING = 'Get the latest news via mail';
  var DEFAULT_SUB = 'WoW Classic news, fresh BiS lists and leveling routes — straight to your inbox. No spam, unsubscribe anytime.';

  function validEmail(v) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v);
  }

  function init(box) {
    var heading = box.getAttribute('data-heading') || DEFAULT_HEADING;
    // data-sub="" means: title only, no sub-text
    var sub = box.hasAttribute('data-sub') ? box.getAttribute('data-sub') : DEFAULT_SUB;
    box.innerHTML =
      '<h3>' + heading + '</h3>' +
      (sub ? '<p>' + sub + '</p>' : '') +
      '<form class="nl-form" novalidate>' +
      '<input type="email" name="email" placeholder="your@email.com" aria-label="Email address" required />' +
      '<input type="text" name="website" class="nl-hp" tabindex="-1" autocomplete="off" aria-hidden="true" />' +
      '<button type="submit">Subscribe</button>' +
      '</form>' +
      '<div class="nl-error" role="alert" aria-live="polite"></div>';

    var form = box.querySelector('.nl-form');
    var input = box.querySelector('input[type="email"]');
    var honeypot = box.querySelector('.nl-hp');
    var error = box.querySelector('.nl-error');

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var email = input.value.trim();
      if (!validEmail(email)) {
        error.textContent = 'Please enter a valid email address.';
        input.focus();
        return;
      }
      error.textContent = '';

      function done() {
        form.outerHTML = '<div class="nl-thanks">✅ Thanks — you’re on the list!</div>';
      }

      function fail() {
        error.textContent = 'Something went wrong — please try again later.';
      }

      if (NEWSLETTER_ENDPOINT) {
        fetch(NEWSLETTER_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'text/plain;charset=utf-8' },
          body: JSON.stringify({ email: email, website: honeypot ? honeypot.value : '' })
        }).then(function (r) {
          return r.json();
        }).then(function (data) {
          if (data && data.ok) { done(); } else { fail(); }
        }, fail);
      } else {
        done();
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.newsletter-cta').forEach(init);
  });
})();
