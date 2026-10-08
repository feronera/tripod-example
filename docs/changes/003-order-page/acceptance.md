# Acceptance: Order status page for customers

References: intent.md (Success measure), spec.md (R1–R19), ux-brief.md, PR: #9 (branch `change/003-order-page`)

Risk: high. Gate 4 needs owner (SuperDev), cross (SuperBiz) and escalation (Lee) signatures.
`gates.log` has no `role=auto` line, so the change has not been auto-merged. This is acceptance before merge.

Third acceptance pass. The first pass proposed reject (incomplete recorded demo, wrong `mobile-5` screenshot). The
second pass proposed reject because four items had no recorded proof: the timeout, session expiry mid-page, focus and
screen-reader behaviour after a retry, and 200% zoom. SuperDev then added `demo/README.md` (recording log with server
flags per state), `demo/evidence.json` (measured values) and four screenshots (commit 841a293, demo files only, no app
or test changes). This file replaces the second pass. It has not passed a gate, so no approval is stale.

Drafted by an agent for SuperBiz. This is a proposed decision. SuperBiz confirms or changes it before signing.

## What the PR changes (plain language)
- Adds a customer order page to the sample app. A customer opens `/orders/<order number>` and sees the order's
  current status, when it was last updated, and every recorded update with the newest first, in Bangkok time.
- Covers every state in the design: loading, success, empty, not found, could not load with "Try again", the support
  line after 3 failed retries, and a redirect to sign-in when nobody is signed in.
- Sign-in is simulated by a clearly marked demo stand-in (`app/auth_demo.py`). It is off unless the server is started
  with `--demo-customer C001`. While it is on, the page shows the banner "Demo sign-in: Customer C001".
- The page only reads data. `app/orders.py` and `app/timefmt.py` are unchanged.
- Size: 44 files, 2809 lines added, none removed (`git diff main...HEAD --shortstat`). This includes the app files,
  tests, change documents and the demo folder (26 screenshots, `run_demo.py`, `README.md`, `evidence.json`).

## Checks run for this acceptance
- Gate 3: `gates.log` has gate 3 owner (dan) and cross (bee) lines. `scripts/gate-check.sh docs/changes/003-order-page 3`
  needed approval in this non-interactive run and was **not run**. SuperDev confirms it before signing.
- `python3 -m unittest discover -s tests` on HEAD (841a293): `Ran 213 tests in 87.297s, OK`.
- `make check` (strength, CODEOWNERS, `gate-check.sh --all`) was **not run** here. SuperDev confirms it on HEAD.
- `git show --stat 841a293`: only `demo/README.md`, `demo/evidence.json` and four PNGs changed. The render output and
  the `handle` runs recorded in the second pass (below) still apply to the same app code.
- Contrast was computed from the colours declared in `app/static/order_page.css` (WCAG formula, not measured in a
  browser): body text `#1a1a1a` on `#ffffff` 17.4:1; banner text `#1a1a1a` on `#fff4d6` 15.88:1; "Try again"
  `#ffffff` on `#1a4d8f` 8.39:1; focus ring `#1a1a1a` on `#ffffff` 17.4:1. The stylesheet declares no other text
  colour, so there is no faint grey text. All are at least 4.5:1.

## Render functions run directly (python3 -c, second pass, same app code)
Seeded the same three updates as `demo/run_demo.py --seed` (A1001: `paid` 6 Oct 09:12, `packing` 7 Oct 14:05,
`shipped` 8 Oct 08:40, all +07:00), then called `render(resolve(lambda: "C001", <id>), "Demo sign-in: Customer C001")`.

**Success: A1001, status 200, `<title>Order A1001</title>`** (`<body>` as returned):
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

**Empty: A1002, status 200, `<title>Order A1002</title>`** (`<body>` as returned):
```html
<aside aria-label="Demo notice"><p>Demo sign-in: Customer C001</p></aside>
<main>
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
</main>
```

**Not found: A1003 (owned by C002), status 404, `<title>Order not found</title>`** (`<body>` as returned):
```html
<aside aria-label="Demo notice"><p>Demo sign-in: Customer C001</p></aside>
<main>
<h1 tabindex="-1">Order not found</h1>
<div role="status"><p>We couldn&#x27;t find this order. Open the order link in your order confirmation email, and check that you are signed in with the account you used to place the order.</p></div>
</main>
```
A1003 (another customer's), A9999 (missing) and `<script>"` (malformed) return equal `Page` values:
`not-found identical (other/missing/malformed): True`.

Also run, for reference, through `app.server.handle` with no signed-in customer (`identify` returns `None`):
- `/orders/A1001`, `/orders/A1003`, `/orders/A9999`: each `303`, `Location: /sign-in?return=/orders/<same id>`,
  body `b''`. Same response shape for an owned, another customer's and a missing order (R11).
- Following the redirect, `/sign-in?return=/orders/A1001`: `404`, title `Order not found`, no demo banner. This is
  the sample's catch-all for unknown paths, because sign-in is outside this repo.
- `/content/orders/A1001` (what "Try again" calls) after sign-out: `303` to `/sign-in?return=/orders/A1001`, empty
  body. This is the server half of E19.
- `order_page.LOAD_TIMEOUT_SECONDS = 10`.

## Demo steps (spec R19): each state and its evidence
Screenshots, `README.md` (server flags per state) and `evidence.json` (measured values) are in
`docs/changes/003-order-page/demo/`, recorded by SuperDev on 2026-10-09 with Playwright in Chrome, one fresh server
per state. Steps 1–7 are unchanged from the second pass; the README now records the flags used for each.

1. **Success**: `/orders/A1001`, `--seed --demo-customer C001`.
   - Expected (R5, R12, R15): banner before the `h1`; `Order A1001`; label; `Updated {datetime}`; time zone note
     directly under it; "Newest first"; rows newest first; earlier-updates note.
   - Actual: `desktop-1-success.png`, `mobile-1-success.png`: exactly this, matching the render output. **Pass.**
2. **Empty**: `/orders/A1002`.
   - Expected (R6): label, no "Updated" line, time zone note at the top of the history section, `history.empty`,
     `history.earlier_note`.
   - Actual: `desktop-2-empty.png`, `mobile-2-empty.png`: exactly this, matching the render output. **Pass.**
3. **Not found (another customer's order)**: `/orders/A1003`.
   - Expected (R7, R12): banner, `Order not found`, the not-found body, no link, no retry, nothing order-specific.
   - Actual: `desktop-3-…`, `mobile-3-…`: exactly this. The render run proves the other-customer, missing and
     malformed pages are identical. **Pass.**
4. **Loading**: `--demo-delay-seconds 30`, captured 1.2 s after opening.
   - Expected (R10): banner, `h1`, "Loading your order…", no order data.
   - Actual: `desktop-4-loading.png`, `mobile-4-loading.png`: exactly this. **Pass.**
5. **Could not load**: `--demo-fail-loads 9`.
   - Expected (R8): banner, `We couldn't load your order`, the error body, "Try again", no support line.
   - Actual: `desktop-5-…`, `mobile-5-…`: exactly this. **Pass.**
6. **Support line after 3 failed retries**: `--demo-fail-loads 9`, Try again ×3.
   - Expected (R9): same error copy, then "Still not working? Contact support at support@shop.example." under the
     body, as plain text, "Try again" still there.
   - Actual: `desktop-6-…`, `mobile-6-…`: exactly this; on mobile it wraps with no horizontal scroll. **Pass.**
7. **A retry that fails, then succeeds** (E18): `--demo-fail-loads 1`, Try again ×1.
   - Expected: same error copy after the failed retry; on success the order appears, no support line.
   - Actual: `*-7a-retry-fails.png`, `*-7b-retry-succeeds.png`: exactly this. **Pass.** (Focus: see step 11.)
8. **10-second timeout** (R8, E16): `--seed --demo-customer C001 --demo-delay-seconds 30`, no forced failure.
   - Expected: could-not-load appears after 10 seconds without a response.
   - Actual: `*-8-timeout-after-10s.png` show the could-not-load state, and `evidence.json`
     `timeout.error_shown_after_ms: 10400`. The server would have answered only after 30 s and no failure was forced,
     so the 10-second timeout produced the error, 0.4 s after the limit. **Pass.** (Second pass: partly shown.)
9. **Not signed in** (R11, E13): no `--demo-customer`.
   - Expected: sent to sign-in with a return to this page; no order data, no order-specific message, no banner; the
     same for every order number.
   - Actual: `*-9-signed-out.png` and the `handle` run: `303` to `/sign-in?return=/orders/A1001`, then the sample's
     404 page (no sign-in page exists here), no banner, no order data. The README now carries the caption the second
     pass asked for, so the screenshot is no longer easy to mistake for the not-found state. **Pass.**
10. **Session expires between first load and "Try again"** (E19): signed in with `--demo-fail-loads 1`, server
    restarted without sign-in, then Try again.
    - Expected: not signed in state, no order data, no banner (R11).
    - Actual: `desktop-11a-before-session-expires.png`: banner and the could-not-load state.
      `desktop-11b-after-session-expires.png`: the same sample 404 page as step 9, no banner, no order data.
      `evidence.json` `session_expired.final_url: http://127.0.0.1:9002/sign-in?return=/orders/A1001`. This
      is the same end point as step 9. **Pass** on desktop; no mobile capture (the behaviour does not depend on width).
      (Second pass: not shown.)
11. **Focus** (R16, E18).
    - Expected (ux-brief Focus management): first load moves focus to the `h1`; pressing "Try again" moves focus to
      the loading text; then to the `h1` on success or the error `h1` on failure. "Try again" reachable by Tab with a
      visible focus outline.
    - Actual: `desktop-10-keyboard-focus-try-again.png`: Tab reaches "Try again", clear dark focus ring. **Pass.**
      `evidence.json` (server `--demo-fail-loads 2`): focused element after the first failure
      `<h1 tabindex="-1">We couldn't load your order</h1>`; after a failed retry, the same error `h1`; after the
      successful retry `<h1 tabindex="-1">Order A1001</h1>`. `desktop-12-focus-after-successful-retry.png` shows the
      success state (the `h1` has no outline by design, so the screenshot alone cannot show focus; the JSON is the
      proof). **Pass for the end points.** The intermediate step (focus on "Loading your order…" while the retry
      runs) is **not recorded**. `order_page.js` line 122 does call `focusFirst("[role='status'] [tabindex='-1']")`,
      but that is code, not demo. Pressing "Try again" with Enter and Space is **not recorded** (it is a native
      `<button>`, so both work by default).
12. **Live region and screen reader** (R16, E17).
    - Expected: the `role="status"` region is cleared and refilled after a failed retry so the same error is
      announced again.
    - Actual: `evidence.json` shows a `role="status"` region holding "Something went wrong. Check your connection and
      try again in a moment." after the first failure and again after a failed retry, and no live region after
      success. That proves the region and its text are right; it cannot prove the re-announcement. **Screen reader
      output is not recorded**, and the README says so plainly. **Not shown.**
13. **320 px and 200% zoom** (R16, E20).
    - Expected: text wraps, no horizontal scroll, at 320 px and at 200% zoom.
    - Actual: `narrow-320-success.png`: success state at 320 px, wraps, nothing cut off. **Pass.**
      `desktop-13-zoom-200.png` (a 1280 px window at 200%, 640 CSS px) shows the success state at double size, all
      text inside the window; `evidence.json` `zoom_200.horizontal_scroll: false`. **Pass for the success state.**
      The support-line state (the longest line, with the email address) was not captured at 200% or at 320 px; the
      390 px mobile capture (step 6) shows it wrapping with no horizontal scroll.
14. **Contrast** (R16).
    - Expected: at least 4.5:1 for all text.
    - Actual: computed from the stylesheet, lowest 8.39:1 (see Checks run). **Not measured on screen**, as the README
      states.

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| 1. "Where is my order" + "order status not showing" chats: from 28 per week (demo data) to 14 per week within 30 days after release | Support tool weekly report, 30 days after release | Cannot be measured before release. No release date, real baseline or report owner is set (intent.md Open questions). This page is a sample; the production page owner is outside this repo (spec decision 5). | Not measurable yet |
| 2. Every 001 ux-brief state is shown in a recorded demo before release: empty, loading, success, not found, could not load (with the 10-second timeout and the support line after 3 failed retries), not signed in / session expired | 26 screenshots, `demo/README.md`, `demo/evidence.json`, plus the render and `handle` runs | Every listed state is recorded, with server flags. The timeout is measured (10.4 s with a 30 s server delay). Session expiry is recorded and ends at sign-in. | **Pass** for the states listed. Two R16 accessibility checks are still unrecorded (screen reader, on-screen contrast); see conditions |

For Success measure 1, SuperBiz states the release date and who pulls the weekly report. The report is then read
30 days after that date. Until a date is set, no measurement date can be given here (rule 5: no invented numbers).

## Decision
Decision: accept, with conditions before release (proposed; SuperBiz confirms)

Reason: The second pass rejected on four gaps in the recording, not on defects in the page. Three of the four are now
closed with recorded, measured proof, and the fourth (focus and screen reader) is half closed:
- Timeout: the error appeared at 10.4 s while the server was set to answer at 30 s with no forced failure
  (step 8), so it is the timeout and not a forced failure.
- Session expiry (E19): recorded before and after, ending at `/sign-in?return=/orders/A1001` with no order data and
  no banner (step 10).
- 200% zoom: recorded, no horizontal scroll (step 13).
- Focus: the end points are recorded (error `h1` after a failure and after a failed retry, `Order A1001` after a
  successful retry, step 11). Screen-reader output is still not recorded.

Every state in Success measure 2 is now on screen with the flags that produced it, every capture matches ux-brief.md
copy and order, and all 213 tests pass on HEAD. What remains is the part of R16 that a browser script cannot record:
what a screen reader actually says, and contrast measured on screen. These are accessibility checks on behaviour the
markup and stylesheet already support (a `role="status"` region refilled with the same text; lowest computed contrast
8.39:1). Success measure 2 says "before release", so they fit as release conditions rather than merge blockers.
Lee's escalation signature is needed for this, because R16 says it is "verified by ... demo" and part of that is
being moved to before release.

If SuperBiz wants the 001 Major closed only with every R16 item recorded, reject is still the valid choice, with the
conditions below as the fix list.

Conditions before release (checked at `scripts/release-check.sh`, not before merge):
1. **Screen reader run (R16, E17).** VoiceOver or NVDA on the sample, with a short written transcript in `demo/`:
   first load announces the `h1`; pressing "Try again" with Enter and with Space; "Loading your order…" announced on
   retry; the error re-announced after each failed retry (1, 2 and 3), and the support line after the 3rd; the
   `h1` announced after the successful retry. This also records the intermediate focus on the loading text that
   step 11 does not show.
2. **Contrast measured on screen (R16).** One measured value per colour pair (banner, body text, "Try again",
   focus ring) from a browser tool, added to `demo/README.md`.
3. **Support-line state at 200% zoom.** One capture of `*-6-after-3-retries` at 200% (the longest line); the second
   pass asked for it and only the success state was recorded.
4. **Success measure 1.** SuperBiz sets the release date and names who pulls the weekly support report; the report
   is read 30 days after that date.

Before signing (SuperDev, not conditions on SuperBiz):
- Confirm `scripts/gate-check.sh docs/changes/003-order-page 3` and `make check` on HEAD (not run here).

Not blocking, for SuperBiz to note:
- Session expiry and the 200% zoom are recorded on desktop only. Neither depends on screen width in the code path
  recorded, so this is noted, not required.
- Signed out and session expired in this sample end on the 404 page titled "Order not found", because no sign-in page
  exists here. The README now says so. In production the real sign-in layer replaces this.
- review.md Minor: `/orders/` (no order number) shows the loading shell first, then not found only after the script
  runs. This matches plan.md. SuperBiz confirms that this is acceptable.
