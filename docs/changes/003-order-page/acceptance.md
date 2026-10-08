# Acceptance: Order status page for customers

References: intent.md (Success measure), spec.md (R1–R19), ux-brief.md, PR: #9 (branch `change/003-order-page`)

Risk: high. Gate 4 needs owner (SuperDev), cross (SuperBiz) and escalation (Lee) signatures.
`gates.log` has no `role=auto` line, so the change has not been auto-merged. This is acceptance before merge.

Drafted by an agent for SuperBiz. This is a proposed decision. SuperBiz confirms or changes it before signing.

## What the PR changes (plain language)
- Adds a customer order page to the sample app. A customer opens `/orders/<order number>` and sees the order's
  current status, when it was last updated, and every recorded update with the newest first, in Bangkok time.
- Covers every state in the design: loading, success, empty, not found, could not load with "Try again", the support
  line after 3 failed retries, and a redirect to sign-in when nobody is signed in.
- Sign-in is simulated by a clearly marked demo stand-in (`app/auth_demo.py`). It is off unless the server is started
  with `--demo-customer C001`. While it is on, the page shows the banner "Demo sign-in: Customer C001".
- The page only reads data. `app/orders.py` and `app/timefmt.py` are unchanged.
- Files: 5 new app files (`app/order_page.py`, `app/server.py`, `app/auth_demo.py`, `app/static/order_page.js`,
  `app/static/order_page.css`), 3 new test files, the change documents, and the demo folder (11 screenshots plus
  `demo/run_demo.py`). In total: 26 files, 2561 lines added, none removed (`git diff main...HEAD --stat`).

## Checks run for this acceptance
- Gate 3: `gates.log` has gate 3 owner (dan) and cross (bee) lines. `scripts/gate-check.sh docs/changes/003-order-page 3`
  and `git hash-object` (to compare the signed blobs) needed approval in this non-interactive run and were **not run**.
  SuperDev confirms both before signing.
- `python3 -m unittest discover -s tests`: `Ran 213 tests in 85.782s, OK`.
- `make check` (strength, CODEOWNERS, `gate-check.sh --all`) was not run here. review.md records a pass at a0df1ce.
  The latest commits (d56fb60, c179e35, 7c34129) came after that.

## Render functions run directly (python3 -c)
Seeded the same three updates as `demo/run_demo.py --seed` (A1001: `paid` 6 Oct 09:12, `packing` 7 Oct 14:05,
`shipped` 8 Oct 08:40, all +07:00), then called `render(resolve(lambda: "C001", <id>), "Demo sign-in: Customer C001")`.

**Success: A1001, status 200** (full `<body>` as returned):
```html
<aside aria-label="Demo notice"><p>Demo sign-in: Customer C001</p></aside>
<main>
<h1 tabindex="-1">Order A1001</h1>
<section aria-labelledby="status-heading">
<h2 id="status-heading">Current status</h2>
<p class="status-label">Shipped</p>
<p>Updated <time datetime="2026-10-08T08:40:00+07:00">8 Oct 2026, 08:40</time></p>
<p>Times are shown in Bangkok time (GMT+7).</p>
</section>
<section aria-labelledby="history-heading">
<h2 id="history-heading">Status history</h2>
<p>Newest first</p>
<ol aria-label="Status history, newest first">
<li>Shipped – <time datetime="2026-10-08T08:40:00+07:00">8 Oct 2026, 08:40</time></li>
<li>Preparing order – <time datetime="2026-10-07T14:05:00+07:00">7 Oct 2026, 14:05</time></li>
<li>Paid – <time datetime="2026-10-06T09:12:00+07:00">6 Oct 2026, 09:12</time></li>
</ol>
<p>Earlier updates are not listed.</p>
</section>
</main>
```
`<title>Order A1001</title>`.

**Empty: A1002, status 200** (`<main>` as returned):
```html
<h1 tabindex="-1">Order A1002</h1>
<section aria-labelledby="status-heading">
<h2 id="status-heading">Current status</h2>
<p class="status-label">Delivered</p>
</section>
<section aria-labelledby="history-heading">
<h2 id="history-heading">Status history</h2>
<p>Times are shown in Bangkok time (GMT+7).</p>
<p>No status updates are listed for this order.</p>
<p>Earlier updates are not listed.</p>
</section>
```

**Not found: A1003 (owned by C002), status 404** (`<body>` as returned):
```html
<aside aria-label="Demo notice"><p>Demo sign-in: Customer C001</p></aside>
<main>
<h1 tabindex="-1">Order not found</h1>
<div role="status"><p>We couldn&#x27;t find this order. Open the order link in your order confirmation email, and check that you are signed in with the account you used to place the order.</p></div>
</main>
```
`<title>Order not found</title>`. The `Page` values for A1003 (another customer's), A9999 (missing) and `<script>"`
(malformed) are equal: `not-found identical (other customer / missing / malformed): True`.

Also run, for reference:
- Signed out (`identify` returns `None`), A1001: `303`, `Location: /sign-in?return=/orders/A1001`, body `b''`, no banner.
- `LoadError(True)`: body, then `<p>Still not working? Contact support at <span>support@shop.example</span>.</p>`,
  then the "Try again" button. The address is in its own `<span>`, the full stop is outside it, and it is not a link.
- A1001 with **no** seeded history: `Empty(order_id='A1001', label='Shipped')`. This is relevant to the
  `mobile-5` screenshot below.

## Demo steps (spec R19): each state and its screenshot
Steps follow plan.md "Order of work" step 10. Screenshots are in `docs/changes/003-order-page/demo/`, taken from the
real server started with `demo/run_demo.py`.

1. **Success**: `/orders/A1001` with `--seed --demo-customer C001`.
   - Expected (R5, R12, R15): banner before the `h1`; `Order A1001`; label; `Updated {datetime}`; time zone note directly
     under it; "Newest first"; 3 rows newest first; earlier-updates note.
   - Actual: `desktop-1-success.png` and `mobile-1-success.png` show exactly this, in this order: Shipped, Updated
     8 Oct 2026, 08:40, then Shipped / Preparing order / Paid with the seeded times. Matches the render output above.
     The mobile layout wraps with no horizontal scroll visible. **Pass.**
2. **Empty**: `/orders/A1002`.
   - Expected (R6): label with no "Updated" line; the time zone note at the top of the history section;
     `history.empty`; `history.earlier_note`.
   - Actual: `desktop-2-empty.png` and `mobile-2-empty.png`: Delivered, no Updated line, then the time zone note,
     "No status updates are listed for this order.", "Earlier updates are not listed.". **Pass.**
3. **Not found (another customer's order)**: `/orders/A1003`.
   - Expected (R7, R12): banner, `Order not found`, the not-found body, no link, no retry, nothing order-specific.
   - Actual: `desktop-3-not-found-other-customer.png` and `mobile-3-not-found-other-customer.png` show this. The
     screenshots do not show the URL, so which order was opened is taken from the file name. The render run above
     proves that the other-customer, missing and malformed responses are identical. **Pass.**
4. **Loading**: shell before the content arrives (for example `--demo-delay-seconds`).
   - Expected (R10): banner, `h1`, "Loading your order…", no order data.
   - Actual: `desktop-4-loading.png` and `mobile-4-loading.png`: banner, `Order A1001`, "Loading your order…",
     nothing else. The browser title is not visible in the screenshots, so it is not confirmed by the demo (it is
     covered by tests per plan.md Proof R10). **Pass.**
5. **Could not load**: `--demo-fail-loads N`.
   - Expected (R8): banner, `We couldn't load your order`, the error body, the "Try again" button, no support line.
   - Actual, desktop: `desktop-5-could-not-load.png` shows exactly this. **Pass.**
   - Actual, mobile: `mobile-5-could-not-load.png` **does not show the could-not-load state.** It shows `Order A1001`,
     Current status Shipped, no Updated line, then the empty-history copy. That is the **Empty** state of A1001 with
     no seeded history (it matches `Empty(order_id='A1001', label='Shipped')` above), so the server for this capture
     was started without `--seed` and without a failing load. **Fail: wrong screenshot.**
6. **Support line after 3 failed retries**: `--demo-fail-loads 4`, press "Try again" 3 times.
   - Expected (R9): same error copy, plus "Still not working? Contact support at support@shop.example." under the body
     as plain text; "Try again" still there.
   - Actual, desktop: `desktop-6-after-3-retries.png` shows exactly this. **Pass.**
   - Actual, mobile: **no screenshot** (there is no `mobile-6`). **Missing.**
7. **10-second timeout**: `--demo-delay-seconds 11`.
   - Expected (R8, E16): could-not-load appears after 10 seconds.
   - Actual: **not recorded.** No screenshot or note shows that the error came from the timeout and not from a forced
     failure. **Missing.**
8. **Failed retry, then success** (E18).
   - Expected: success or empty state appears, the support line is gone, focus moves to the `h1`.
   - Actual: **not recorded. Missing.**
9. **Not signed in / session expired**: start without `--demo-customer`; then restart without the flag and press
   "Try again".
   - Expected (R11, E19): redirect to `/sign-in?return=/orders/A1001`, no order data, no banner, the same for every
     order number.
   - Actual: **no screenshot on desktop or mobile.** The render run above shows the 303 with an empty body and no
     banner, but intent.md Success measure 2 asks for this state in the recorded demo. **Missing.**
10. **Keyboard, focus, screen reader, contrast, 320 px and 200% zoom** (R16; plan.md step 10).
    - Expected: "Try again" reachable by Tab with a visible focus outline; focus moves to the `h1`; the live region
      re-announces after a failed retry; contrast of at least 4.5:1; no horizontal scroll at 320 px and 200% zoom.
    - Actual: **not recorded.** The mobile screenshots show wrapping text without horizontal scroll, but they are not
      320 px or 200% zoom captures, and no focus, keyboard or screen-reader result is noted. review.md asks for the
      screen-reader check on E17 and for the JS to be exercised before acceptance. **Missing.**

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| 1. "Where is my order" + "order status not showing" chats: from 28 per week (demo data) to 14 per week within 30 days after release | Support tool weekly report, 30 days after release | Cannot be measured before release. No release date, real baseline or report owner is set (intent.md Open questions). This page is a sample, and the production page owner is outside this repo (spec decision 5). | Not measurable yet |
| 2. Every 001 ux-brief state is shown in a recorded demo before release: empty, loading, success, not found, could not load (with the 10-second timeout and the support line after 3 failed retries), not signed in / session expired | Screenshots in `demo/` plus the render output above | Shown: success, empty, not found, loading (desktop and mobile); could not load and the support line (desktop only). Not shown: could not load on mobile (wrong screenshot), the support line on mobile, the 10-second timeout, a retry that then succeeds, not signed in / session expired, and the R16 keyboard/focus/screen-reader/zoom checks. | **No** |

For Success measure 1, SuperBiz states the release date and who pulls the weekly report. The report is then read
30 days after that date. Until a date is set, no measurement date can be given here (rule 5: no invented numbers).

## Decision
Decision: reject (proposed; SuperBiz confirms)

Reason: The page itself behaves as designed in every state that was captured. The success, empty, not-found, loading,
could-not-load and support-line screens match ux-brief.md and spec.md copy and order. The direct render output matches
too, including identical not-found responses for another customer's, a missing and a malformed order, and the empty
signed-out redirect. All 213 tests pass. But this change exists to close change 001's open Major with a **recorded
demo of every state** (intent.md Success measure 2, spec R19), and that recording is incomplete. One screenshot is
wrong, and the timeout, signed-out, retry-then-success and accessibility parts were not recorded. Accepting now would
leave the 001 Major open while marking it closed.

What must be fixed before acceptance:
- Replace `mobile-5-could-not-load.png`: it shows the Empty state of an unseeded A1001, not could-not-load. Re-take it
  with `run_demo.py --seed --demo-customer C001 --demo-fail-loads 4`.
- Add `mobile-6-after-3-retries.png` (support line on mobile).
- Record the 10-second timeout (`--demo-delay-seconds 11`): a screenshot after 10 seconds plus a note of the elapsed time.
- Record a failed retry followed by success (E18): the support line is gone, and focus is on the `h1`.
- Record not signed in on desktop and mobile (server started without `--demo-customer`): the redirect to
  `/sign-in?return=/orders/A1001`, no banner, no order data. Also record session expiry mid-page (restart without the
  flag, then press "Try again") (E19).
- Record the R16 checks: Tab to "Try again" with a visible focus ring, focus moving to the `h1`, a screen-reader
  announcement after a failed retry, contrast, and 320 px and 200% zoom captures.
- SuperDev confirms `scripts/gate-check.sh docs/changes/003-order-page 3` and `make check` on the current HEAD.

Not blocking, for SuperBiz to note:
- Success measure 1 needs a release date and an owner for the weekly report (intent.md Open questions).
- review.md Minor: `/orders/` (no order number) shows the loading shell first, then not found only after the script
  runs. This matches plan.md. SuperBiz confirms that this is acceptable.
