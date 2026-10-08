# Plan: Order status page for customers

References: intent.md, spec.md, ux-brief.md, `docs/changes/001-order-history/` (spec.md, review.md, acceptance.md)

Scope follows the decisions at the end of spec.md:
1. The sign-in check runs first. With no signed-in customer, the page shows the "not signed in" result before any order lookup.
2. The demo stand-in is the only source of the customer id. Lee reviews it at gates 2 and 4.
3. The stand-in is off unless the server starts with `--demo-customer <id>`. The banner is on exactly when the stand-in is on. To show "not signed in", start the server without the flag.
4. Equal response time for "not found" is not measured.
5. This repo builds the reference sample page, and its demo closes the open 001 Major.
6. The shared GitHub login is a known demo limit.
7. intent.md is not edited.

`app/orders.py` and `app/timefmt.py` are not changed (spec Out of scope).

Design rule: everything a customer can see is produced by pure functions in `app/order_page.py`. These functions take plain values (a view record and a banner string) and return a `Page` value (status, headers, body). Tests call them directly without a server. `app/server.py` is a thin adapter: it parses flags, matches the path, calls one pure function, and writes the `Page` to the socket.

## Data shape
1. **One record per state.** The page's outcome is one of six immutable records (`typing.NamedTuple`) in
   `app/order_page.py`. Each state carries only the fields it is allowed to show, so some mistakes cannot be written at all. For example, a not-found page cannot carry order data (R7), the empty state has no "Updated" time (R6), and signed out has no banner and no body (R11, R12):
   ```python
   class Loading(NamedTuple):   order_id: str | None          # None → title "Loading order" (E4)
   class Success(NamedTuple):   order_id: str; label: str; updated: dict | None; history: tuple  # history non-empty
   class Empty(NamedTuple):     order_id: str; label: str     # no `updated`, no `history` (E1)
   class NotFound(NamedTuple):  pass                          # no fields: nothing order-specific (R7, E3–E6, E11)
   class LoadError(NamedTuple): show_support: bool           # True only after 3 failed retries (R9)
   class SignedOut(NamedTuple): return_path: str             # built by the server from the matched route, never from the query
   ```
   `updated` and each history row's `time` are the `{"text", "iso"}` dicts already returned by
   `status_history` / `time_view` (R15). History rows are `(label, time)` tuples, newest first as given (E9).
2. **The order of decisions is one function**: `resolve(identify, order_id, load) -> view`. It contains the only branching in the request path, in a fixed order (R3, E13, E14):
   | Step | Outcome | View |
   |---|---|---|
   | `identify()` raises | stand-in failed, same for every order id | `LoadError(False)` (E14) |
   | `identify()` returns `None` | not signed in; `load` is never called | `SignedOut(return_path)` (R3, R11) |
   | `load(customer_id, order_id)` raises `OrderNotFound` | missing, another customer's, malformed | `NotFound()` (R7) |
   | `load(...)` raises anything else | could not load | `LoadError(False)` (R8) |
   | result has no history | | `Empty(...)` (R6) |
   | result has history | | `Success(...)` (R5, E2) |
   `load` defaults to `app.orders.status_history`, which is the only domain function the page imports (R1). The customer id is the value returned by `identify()`, and `resolve` takes no request data, so a query string, header or cookie cannot supply a customer id (R2, E12).
3. **Rendering is a dispatch table, not scattered `if`s**: `_RENDER = {Loading: ..., Success: ..., Empty: ..., NotFound: ..., LoadError: ..., SignedOut: ...}` and `render(view, banner) -> Page`.
   `Page(status: int, headers: tuple[tuple[str, str], ...], body: bytes)`.
   | View | HTTP status | Title / `h1` | Banner |
   |---|---|---|---|
   | Loading | 200 | `Order {id}` or `Loading order` | yes, if demo |
   | Success, Empty | 200 | `Order {id}` | yes, if demo |
   | NotFound | 404 | `Order not found` | yes, if demo |
   | LoadError | 503 | `We couldn't load your order` | yes, if demo |
   | SignedOut | 303, `Location: /sign-in?return=<quoted path>`, empty body | n/a | never (R11, R12) |
   Every response gets the same fixed header set: `Content-Type: text/html; charset=utf-8`, `Cache-Control: no-store`,
   `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and
   `Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'`.
4. **Copy is one table**, `COPY: dict[str, str]`. Its keys are exactly the ux-brief "Copy" keys, and its text is copied exactly (R14). `demo.banner` is the template `Demo sign-in: Customer {customer_id}`, which gives the approved text for `C001`. Every value written into HTML passes through one helper, `_esc = html.escape(..., quote=True)` (R17, E5, E8).
5. **Client state is small and lives in one place.** `GET /orders/{id}` returns `render(Loading(id))`, the shell page. The shell includes `/static/order_page.js`, which:
   - fetches `GET /content/orders/{id}` with a 10-second `AbortController` timeout (R8, E16);
   - parses the returned full document;
   - swaps in its `<main>` content and `<title>`, then moves focus to the `h1` (R16).

   The two could-not-load variants are not written in JS. The shell embeds `render`'s own `LoadError(False)` and `LoadError(True)` markup as `<template>` elements. JS chooses between them using one counter, `failedRetries`; the support line appears when `failedRetries >= 3` (R9, E17), and success resets everything (E18). A 303/401 from the content route reloads the shell, and the shell route then redirects to sign-in (E19). The constants `LOAD_TIMEOUT_SECONDS = 10` and `SUPPORT_AFTER_FAILED_RETRIES = 3` sit in `order_page.py` and reach JS through `data-` attributes, so the numbers are defined once and tests can read them.
6. **The demo stand-in is one value**, in `app/auth_demo.py`. This file is clearly marked demo-only. Its name deliberately matches `app/auth*` in `docs/risk-paths`, so CODEOWNERS requires escalation review for any later edit (spec concern 3):
   ```python
   class DemoSignIn(NamedTuple):      # DEMO ONLY – never wire into production
       customer_id: str
       def identify(self): return self.customer_id
       @property
       def banner(self): return COPY["demo.banner"].format(customer_id=self.customer_id)
   NO_SIGN_IN = (lambda: None, None)  # (identify, banner) when the flag is absent: everyone is signed out
   ```
   `identify` and `banner` always come from the same source, so a demo banner without the stand-in, or the stand-in without its banner, cannot happen (R12, R13). The demo-only fault switches `--demo-fail-loads N` (the next N loads raise) and `--demo-delay-seconds S` (sleep before load) wrap `load`. They are accepted only together with `--demo-customer`, and argparse rejects them otherwise (R13, R19).
7. **Routing is a fixed table on the raw path.** The path is split with `urllib.parse.urlsplit` and the query is dropped. The order id is the raw path segment: it is not URL-decoded, not trimmed and not case-folded, so `A%31001`, `a1001` and ` A1001` stay not found (E5, E6):
   | Pattern | Kind | Sign-in checked |
   |---|---|---|
   | `^/orders/([^/]*)$` | shell (Loading) | yes |
   | `^/content/orders/([^/]*)$` | content (`resolve` → view) | yes |
   | `/static/order_page.js`, `/static/order_page.css` | fixed allowlist of bytes, no filesystem path from the URL | no (no data) |
   | anything else | `NotFound()` after the sign-in check | yes |
   `handle(method, path, identify, load, banner) -> Page` is a module-level pure function in `app/server.py`. Any method other than GET returns 405 with `Allow: GET` and never calls `identify` or `load` (E15, R4). The `BaseHTTPRequestHandler` subclass only calls `handle` and writes the result. Its `log_message` logs only the method, route kind and status, never the path or order id (AGENTS.md rule 6).

## Throughput checkpoint
- Blocking first steps: the failing tests in `tests/test_order_page.py` and `tests/test_order_server.py`, committed and then locked. They fix the interface in Data shape: the view records, `resolve`, `render`, `Page`, `COPY`, `handle`, flag parsing and the template ids. `.pod/lock-tests` already exists from earlier work, so a human removes it before `/superdev:test-first` and re-creates it after the test commit (AGENTS.md rule 2).
- Independent workstreams: part A (pure rendering plus static JS/CSS) and part B (server, routing, demo stand-in) can be built in parallel once the tests are locked. B depends only on A's frozen interface, not on its output.
- Shared mutable state: `_ORDERS` and `_HISTORY` in `app/orders.py` are read by the page and never written (R4). Tests seed history through `set_status` inside `patch.dict(orders._ORDERS)` and `patch.dict(orders._HISTORY, clear=True)`, so the 001 tests still see the original sample data (R18). The interface between A and B is defined by the locked tests, not edited by both parts.
- Smallest safe decomposition: six units, each ending with `make test`:
  1. `COPY`, the view records, `_esc` and `render` for NotFound, LoadError and SignedOut → their render tests pass.
  2. `render` for Loading, Empty and Success → its tests pass.
  3. `resolve` → its order-of-checks tests pass.
  4. `auth_demo` plus flag parsing → R13 tests pass.
  5. `route` and `handle` → server tests pass.
  6. Static JS/CSS → demo.

  Each step ends with `make test`.

## Parallel parts
### A: page rendering
files: app/order_page.py, app/static/order_page.js, app/static/order_page.css
### B: server and demo sign-in
files: app/server.py, app/auth_demo.py

## Files to change
| File | What changes | Requirement |
|---|---|---|
| `tests/test_order_page.py` (new) | Failing tests for `COPY`, `render` in every state, `resolve` order of checks, escaping, Bangkok times and markup accessibility | R1, R3, R5–R10, R12, R14–R17, E1–E11, E13, E14, E17, E18 |
| `tests/test_order_server.py` (new) | Failing tests for `handle` and `route`: no customer id from query/header/cookie, non-GET rejected, signed-out redirect, demo flags, no data change. Also one `ThreadingHTTPServer` on port 0 smoke test | R1–R4, R11–R13, E4–E6, E12, E15, E19 |
| `app/order_page.py` (new) | View records, `COPY`, `_esc`, `resolve`, `render`, `Page`, timing constants; imports only `status_history`, `OrderNotFound` from `app.orders` | R1, R3, R5–R10, R12, R14–R17 |
| `app/static/order_page.js` (new) | Fetch with 10-second timeout, swap `main`/title, live-region refill, focus moves, `failedRetries` and support template, reload on 401/303 | R8–R10, R16 |
| `app/static/order_page.css` (new) | Contrast of at least 4.5:1, visible focus outline, `overflow-wrap: anywhere`, no horizontal scroll at 320 px / 200% zoom | R16, E20 |
| `app/auth_demo.py` (new, matches `app/auth*` risk path) | `DemoSignIn`, `NO_SIGN_IN`, demo-only labelling | R2, R12, R13 |
| `app/server.py` (new) | `route`, `handle`, `parse_args`, demo fault wrappers, thin handler, `main()`; binds `127.0.0.1` by default | R1–R4, R11, R13, E15 |
| `tests/test_orders.py`, `tests/test_order_history.py`, `tests/test_status_report.py` | No change (must pass as is) | R18 |
| `app/orders.py`, `app/timefmt.py` | No change | R1, R18 |
| `docs/changes/003-order-page/acceptance.md`, `runbook.md` (gate 4) | Recorded demo of every state, plus how to start the sample with and without `--demo-customer` | R19 |

`app/auth_demo.py` matches `docs/risk-paths:4`, which agrees with `Risk: high` in intent.md. No other risk path is touched. The 001 documents are not edited (rule 7): the 001 Major is closed by the demo recorded in this change's acceptance.md, which references 001 `review.md:21-24` and `acceptance.md:101-103`.

## Order of work
1. A human removes the stale `.pod/lock-tests`. Then run `/superdev:test-first` to write both test files from E1–E20 and R1–R18.
   Confirm every test fails for the right reason (missing module or wrong value). Run `make strength`, then commit `test(003): ...`.
2. Lock the tests (`touch .pod/lock-tests`).
3. Unit A1: `COPY`, view records, `_esc`, `Page`, and `render` for NotFound / LoadError (both variants) / SignedOut.
   `make test` passes for those tests. Commit `feat(003): ...`.
4. Unit A2: `render` for Loading, Empty and Success (sections, `ol`, `<time>`, banner `aside` before `main`, templates in the shell). `make test`, then commit.
5. Unit A3: `resolve` with the order-of-checks table. `make test`, then commit.
6. Unit B1: `app/auth_demo.py` and `parse_args`, with fault flags accepted only with `--demo-customer`. `make test`, then commit.
7. Unit B2: `route`, `handle` and the thin handler in `app/server.py`. All tests pass, and the 001/002 tests are unchanged. Commit.
8. Unit A4: `order_page.js` and `order_page.css`. `make test`, then a manual run with `python3 -m app.server --demo-customer C001`. Commit.
   (Units A1–A4 and B1–B2 may run as the two parallel parts above, after step 2.)
9. `make check`, then `/superdev:review` with escalation (Lee) reviewing `app/auth_demo.py` and `app/server.py`.
10. Record the R19 demo in acceptance.md: every state, the 10-second timeout (`--demo-delay-seconds 11`), 3 failed retries
    (`--demo-fail-loads 4`), a failed retry followed by success, signed out (no flag), session expiry (restart without the flag, then press
    "Try again"), keyboard, screen reader, contrast, 320 px and 200% zoom.

## Risks
- **The stand-in reaches production.** Reduce:
  - the stand-in is off by default and turned on only by an explicit flag;
  - the banner comes from the same object, so the stand-in cannot be on silently;
  - it lives in a risk-path file under CODEOWNERS;
  - a test asserts that only `app/server.py` imports `app.auth_demo`;
  - the sample has no production entry point.

  The real sign-in layer replaces `identify` and will need request data (a verified session). Its design is a separate high-risk change.
- **Customer id taken from the browser** (R2). Reduce: `handle` and `resolve` never receive headers, cookies or the query string. A test sends `?customer_id=C002`, an `X-Customer-Id` header and a cookie, and still sees only C001's orders.
- **Existence leak.** Reduce:
  - `NotFound` has no fields;
  - one `OrderNotFound` path inside `status_history`;
  - raw ids are not normalized;
  - tests compare missing, other-customer and malformed responses byte for byte.

  Response timing is not measured (decision 4).
- **XSS through the order id, a status code or a label.** Reduce:
  - every value passes through `_esc`;
  - the strict CSP allows no inline script or style;
  - JS inserts only same-origin server-escaped markup and sets text with `textContent`;
  - tests cover `<script>` and `"` in an id and in a status code.
- **Open redirect through `return`.** Reduce: `return_path` is rebuilt from the matched route and quoted. The query string is never copied into `Location`.
- **Loading, timeout, retry and focus are JavaScript and not unit-testable with the standard library.** Reduce:
  - the markup, the two error variants and the constants are rendered and tested in Python;
  - JS only swaps markup and counts;
  - behavior is proven by the recorded demo (R19).

  Without JS, the shell stays on "Loading your order…". This is accepted for the sample, and the content URL still works on its own.
- **Test state leaking into the 001/002 tests.** Reduce: tests seed history only inside `patch.dict` contexts. R4 tests compare deep copies of `_ORDERS` and `_HISTORY` before and after requests.
- **Weak tests on `handle` or the handler class.** `test-strength.sh` checks module-level functions only. Reduce: keep the logic in module-level `resolve`, `render`, `route`, `handle` and `parse_args`, and keep the handler class as a pass-through.
- **History lost on restart** (spec concern 8). Many orders will show the empty state. This is a known limit, and the copy never shows a guessed time.

## Proof
- `make test` and `make strength` pass; `make check` passes.
- R1: `render(resolve(...))` for C001 / A1001 with seeded history returns 200 and the success page. A test patches `app.orders.set_status` to raise, runs every route, and nothing fails. A source check asserts `order_page.py` and `server.py` import nothing from `app.orders` except `status_history` and `OrderNotFound`.
- R2, E12: `handle` with `?customer_id=C002` and the raw HTTP smoke test with an `X-Customer-Id: C002` header and a cookie still show C001's A1001 and return not found for A1003.
- R3, E13: an `identify` that returns `None` and a `load` that records calls: `SignedOut`, and `load` is never called.
- R4, E15: deep copies of `_ORDERS`/`_HISTORY` are equal before and after requests in every state. POST, PUT and DELETE return 405 with `Allow: GET`.
- R5, E2, E9, E10: Success HTML contains, in order:
  - the `h1` and `<title>` `Order A1001`, the label, the `Updated …` line, then `history.timezone`;
  - `Newest first`, then the `ol aria-label="Status history, newest first"` with rows newest first (the later-recorded row first on a tie);
  - `history.earlier_note`.

  The 18:30 UTC row shows `10 Oct 2026, 01:30`. When the latest update is not the current status, there is no `Updated` line.
- R6, E1: `Empty` shows the label, no `Updated`, then `history.timezone`, `history.empty` and `history.earlier_note`, in that order.
- R7, E3–E6, E11: `Page` values for `A9999`, A1003, A1004, `""`, a 1000-character id, `a1001`, ` A1001`, `A%31001`, `A;1`, `%00` and `<script>` are byte-identical: status 404, the same headers and the same body. The body contains no id.
- R8, E14, E16: `load` raises `RuntimeError` → 503 and could-not-load copy with "Try again". A raising `identify` gives the same `Page` for every id. 10-second timeout: demo.
- R9, E17, E18: `LoadError(True)` adds the support line under the body with the address in its own `<span>` and the full stop outside it, not a link. `LoadError(False)` has no support line. The shell embeds both templates and `data-support-after="3"`. Retry behavior: demo.
- R10: `Loading("A1001")` shows only `page.loading` in `role="status"`, with title `Order A1001`. `Loading(None)` has title `Loading order`. Neither contains order data.
- R11, E19: shell and content routes for A1001, A1003 and A9999 with no sign-in return 303 to `/sign-in?return=…`. The responses differ only in the quoted path, the body is empty, and there is no banner. Expiry mid-page: demo.
- R12: the banner appears exactly once as `<aside aria-label="Demo notice">`, before `<main>` and the `h1`, with identical text, in Loading, Empty, Success, NotFound and LoadError. It never appears in SignedOut and never appears without `--demo-customer`.
- R13: `parse_args([])` gives no stand-in and no banner. `--demo-fail-loads` or `--demo-delay-seconds` without `--demo-customer` exits with an argparse error. `app.auth_demo` is imported only by `app/server.py`. Demo: start with and without the flag.
- R14, E7: each `COPY` value equals the ux-brief text. An `on_hold` order shows `on_hold` in both current status and history.
- R15: every time is `<time datetime="…+07:00">` with `time_view` text.
- R16: the markup test checks:
  - one `h1` per state, with `tabindex="-1"`;
  - two `h2`;
  - the `ol` aria-label;
  - `role="status"`;
  - the only `<button>` is "Try again", and there is no `<a>` in the body.

  Focus, contrast, keyboard, 320 px and 200% zoom: demo.
- R17, E5, E8: an id `A<script>"` and a status code `<b>x</b>"` appear only escaped.
- R18: `tests/test_orders.py`, `tests/test_order_history.py` and `tests/test_status_report.py` pass, and `git diff main -- tests/test_orders.py tests/test_order_history.py tests/test_status_report.py app/orders.py app/timefmt.py` is empty.
- R19: the recorded demo in acceptance.md covers every state in intent.md Success measure 2 and 001 R9–R13 / E13–E18.

## Rollback
- The change only adds files. Revert the squash-merge commit: `git revert <merge-commit>`, open a PR, run `make check`, and merge it by the high-risk route.
- No data, schema or stored history is touched, so nothing else needs undoing. A running sample server must be stopped (Ctrl+C). The page has no other callers.
- Check afterwards: `make test` passes, `app/orders.py` behavior is unchanged (the 001 tests are green), and `app/auth_demo.py` is gone. A human records the revert with `scripts/mark-revert.sh` (agents do not run it).

## Open questions
- `/sign-in` is outside this repo and is not served by the sample. In the demo, the signed-out state is shown as a 303 to `/sign-in?return=/orders/A1001`, so the browser lands on a 404. Is that acceptable for the recorded demo, or should the sample serve a plain placeholder at `/sign-in`, which needs new copy from SuperBiz?
- With the stand-in on, a customer id other than `C001` would change the banner text (`Demo sign-in: Customer C002`). The approved copy names only C001. Should the demo use only `C001`?
- How the real sign-in layer passes a verified customer id (for example, a trusted proxy header) is out of scope here. Who designs it for production?

## Summary for SuperBiz
1. We will build the order page from the earlier design in this sample app: customers see their order's current status and its list of updates, newest first, in Bangkok time.
2. Customers opening their order link will see every state from the design: loading, empty, success, not found, could not load with "Try again" and the support line after 3 failed retries, and the sign-in redirect. In the sample, a clear "Demo sign-in: Customer C001" banner shows that sign-in is simulated.
3. Sign-in in this sample is a stand-in that is off unless someone turns it on, and a reviewer (Lee) must check it. Loading, timeout and retry behavior is proven by a recorded demo rather than automated tests, and many orders will show "No status updates" after a restart.
