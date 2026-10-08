blockers: 0
majors_open: 2
second_opinion: agree
reviewed_head: a0df1ce8114c65499a3d9d207a476e63bf9f3084

# Review: Order status page for customers

The first 4 lines are a header read by `scripts/auto-merge-check.sh`. Do not rename the keys.
`second_opinion: agree` means reviewer-second found no Blocker that the main reviewer missed and does not dispute the "no Blocker" result.

Compared with `origin/main` (fetched at review time). There were three reviewer lenses (security, correctness, tests and edge cases), then a re-review of the fix commit, then reviewer-second on the full diff. Tests were locked (`.pod/lock-tests`) throughout, and no file in `tests/` was edited.

Risk is high. Gate 4 needs the escalation signature (Lee). Lee should review `app/auth_demo.py` and `app/server.py` (plan.md Order of work 9).

## Blocker
- none

## Major
Fixed in a0df1ce (`fix(003): review Majors ...`):
- `app/server.py:58-61` (old): there was a redirect loop when signed out (R11, E19).
  - `/orders/A1001` redirected with a 303 to `/sign-in?return=/orders/A1001`. `/sign-in` routed as "other", so it redirected with a 303 to `/sign-in?return=/`, which redirected to itself.
  - The browser stopped with "too many redirects". The plan expected a 404, and the R19 demo of "not signed in / session expired" would have shown a browser error.
  - Fixed: a signed-out request to an unknown path now gets the not-found page with no banner (`app/server.py:62-64`).
- `app/server.py:36` (old): a request target that `urlsplit` cannot parse raised an unhandled `ValueError` (E5 "never an unhandled error").
  - Example: `GET http://[/orders/A1001`. socketserver then logged a traceback that included the client address.
  - Fixed: `route()` returns `("other", None)` for such a target (`app/server.py:35-38`).
- `app/static/order_page.js:92-94` (old): while a retry was loading, the tab kept the error title "We couldn't load your order" (R10).
  - Fixed: the script now saves the shell's title at start-up and restores it during the retry.
- `app/static/order_page.js:20-23` (old): each state change replaced the `role="status"` element (R16, E17 "cleared and refilled").
  - Fixed: the live region now stays in the page and only its contents are refilled. Re-announcement is still demo-verified (R16).

Open (human decision needed):
- `app/server.py:35-38, 62-64`: the two server fixes above have no regression test (spec E5, E19; AGENTS.md rule 9).
  - The tests are locked, so no test could be added. If either hunk is reverted, `make check` stays green.
  - To close this, a human removes `.pod/lock-tests`. Then add tests to `tests/test_order_server.py`:
    1. `handle("GET", "http://[/orders/A1001", ...)` returns the not-found page.
    2. Signed out, `GET /sign-in?return=/orders/A1001` returns the 404 not-found page, not a 303.

    Re-lock the tests afterwards.
- `app/server.py:62-64` differs from plan.md:76. The plan says "anything else → `NotFound()` after the sign-in check", which implies a redirect when signed out. The code now returns 404 with no banner when signed out on an unknown path, which is what breaks the loop.
  - plan.md has passed gate 3 and was not edited (rule 7).
  - SuperDev decides one of two things:
    - accept the deviation as recorded here, or
    - update plan.md (including its Open question on `/sign-in`) and re-sign gate 3.
  - A side effect: signed out, `/orders/A1001/x` (an order number containing `/`) gets 404, while `/orders/A1001` gets the sign-in redirect.
    - Before this fix it got a 303 to `return=/`, so it was not identical to `/orders/A1001` before either.
    - The response depends only on the shape of the path, so it does not reveal whether an order exists.

## Minor
- `app/server.py:58, 69-77`: when the stand-in raises on the shell route `/orders/{id}`, the response is the full 503 page, which has no script, so its "Try again" does nothing (R9, E14).
  - This can't happen today: `DemoSignIn.identify` cannot raise.
  - The test at `tests/test_order_server.py:216` covers the content route only.
- `app/server.py:69-77` and `app/order_page.py:95-100`: the sign-in-first check is duplicated in `_signed_in_view` and `resolve`. `SignedOut("/")` in `_signed_in_view` is now a value `handle` never uses.
- `app/static/order_page.js:47`: `live.replaceChildren()` has no visible effect, because line 48 refills the region in the same task.
  - The repeat announcement in E17 comes from the "Loading your order…" text that appears between attempts. The R19 demo must check with a screen reader.
- `app/server.py:86-88, 108`: `--host 0.0.0.0 --demo-customer C001` is allowed, which exposes the stand-in to the network. Question for Lee: refuse `--demo-customer` with a host that is not loopback?
- `app/server.py:95-108`: `--demo-customer ""` is accepted. Every order is then "not found" and the banner reads `Demo sign-in: Customer `.
- `app/server.py:143, 152`: some responses come from `BaseHTTPRequestHandler.send_error` and skip the fixed header set (`CSP`, `nosniff`, `no-store`):
  - methods without a `do_*` handler (TRACE, CONNECT);
  - malformed request lines;
  - request lines that are too long (414).

  Every response also carries the `Server: BaseHTTP/… Python/…` header.
- `app/order_page.py:85-86`: the CSP has no `base-uri 'none'` and no `form-action 'none'` (defence in depth; nothing is exploitable today).
- `app/server.py:77-80`: `_static` does not handle a missing file. It would raise and drop the connection. The files are in the repo.
- `app/server.py:27-30`: in the route regexes, `$` also matches before a trailing `\n`. A real request line cannot carry a newline, so this matters only when `handle` is called directly. `\Z` would be stricter.
- `app/server.py:48-51`: HEAD returns 405. This matches "GET only" in E15. It is recorded as a deliberate choice.
- `tests/test_order_page.py:567`: the focus-outline regex also matches `[tabindex="-1"]:focus { outline: none; }`. Deleting the visible `:focus-visible` rule would not fail the test.
- `tests/test_order_page.py:569-576`: the script test checks only for words in the file. It does not check:
  - `data-load-timeout-seconds`;
  - `data-support-after`;
  - `redirect: "manual"`.
- `tests/test_order_server.py:414-415`: the real-socket test compares the A1003 and A9999 responses by body only. The direct `handle` test at `:227-239` does the full comparison.
- `tests/test_order_server.py:243-247`: E4 on `/orders/` shows the loading shell first, and not found only after the script runs (no not found without JS). This matches plan.md. SuperBiz confirms it at acceptance.
- `app/order_page.py:137`: escaping of the banner text has no test. The value comes from the operator and is demo-only.
- `tests/_html.py`: this test helper is not listed in plan.md "Files to change".

## Second opinion (reviewer-second)
- Verdict: no-blocker. It agrees with the "no Blocker" result.
- It found the same open Majors independently:
  - no tests for the fix commit's server behaviour;
  - the signed-out unknown-path behaviour differs from plan.md:76.
- Its Minors overlap the list above: duplicated sign-in check, stand-in failure on the shell route, `_static` with a missing file, HEAD returning 405, `$` vs `\Z`, `tests/_html.py` scope.
- It could not run `make check` itself. The checks below were run in this session.

## Checks
- `make check`: pass at a0df1ce (211 tests OK, CODEOWNERS OK, `gate-check.sh --all` OK; 003 has passed up to gate 3).
- `scripts/test-strength.sh`: pass ("checked 106 tests, no weak tests").
- The JS change was not syntax-checked by machine (`node --check` needed approval in this run). Exercise it in the R19 demo before acceptance.
