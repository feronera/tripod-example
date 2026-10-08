// Order page shell (change 003). Loads /content/orders/{id} and swaps in its <main>.
// All copy and markup come from the server: the page itself or the shell's <template>s.
// The timeout and the support limit come from data- attributes set in app/order_page.py.
(function () {
  "use strict";

  var main = document.querySelector("main[data-load-timeout-seconds]");
  if (!main) {
    return;
  }
  var timeoutMs = Number(main.getAttribute("data-load-timeout-seconds")) * 1000;
  var supportAfter = Number(main.getAttribute("data-support-after"));
  // The raw path segment is reused as is: the server does not decode it either.
  var contentUrl = location.pathname.replace(/^\/orders\//, "/content/orders/");
  var loadingNodes = Array.prototype.map.call(main.childNodes, function (node) {
    return node.cloneNode(true);
  });
  var failedRetries = 0;

  function show(nodes, title) {
    main.replaceChildren.apply(main, nodes);
    document.title = title;
  }

  function focusFirst(selector) {
    var el = main.querySelector(selector);
    if (el) {
      el.focus();
    }
  }

  function showLoaded(html) {
    var doc = new DOMParser().parseFromString(html, "text/html");
    var loaded = doc.querySelector("main");
    if (!loaded) {
      throw new Error("no main");
    }
    var nodes = Array.prototype.map.call(loaded.childNodes, function (node) {
      return document.importNode(node, true);
    });
    show(nodes, doc.title);
    failedRetries = 0; // success resets everything (E18)
    focusFirst("h1");
  }

  function showFailed(isRetry) {
    if (isRetry) {
      failedRetries += 1;
    }
    var id = failedRetries >= supportAfter ? "tpl-load-error-support" : "tpl-load-error";
    var fragment = document.getElementById(id).content.cloneNode(true);
    var h1 = fragment.querySelector("h1");
    show(Array.prototype.slice.call(fragment.childNodes), h1 ? h1.textContent : document.title);
    focusFirst("h1");
  }

  function load(isRetry) {
    var controller = new AbortController();
    var timer = setTimeout(function () {
      controller.abort();
    }, timeoutMs);
    fetch(contentUrl, {
      signal: controller.signal,
      credentials: "same-origin",
      redirect: "manual",
      headers: { Accept: "text/html" },
    })
      .then(function (response) {
        // Signed out meanwhile (E19): reload the shell, whose route redirects to sign-in.
        if (response.type === "opaqueredirect" || response.status === 303 || response.status === 401) {
          location.reload();
          return;
        }
        if (response.status !== 200 && response.status !== 404) {
          throw new Error("status " + response.status);
        }
        return response.text().then(showLoaded);
      })
      .catch(function () {
        showFailed(isRetry);
      })
      .finally(function () {
        clearTimeout(timer);
      });
  }

  main.addEventListener("click", function (event) {
    var button = event.target.closest("button[data-action='retry']");
    if (!button) {
      return;
    }
    show(loadingNodes.map(function (node) {
      return node.cloneNode(true);
    }), document.title);
    focusFirst("[role='status'] [tabindex='-1']");
    load(true);
  });

  load(false);
})();
