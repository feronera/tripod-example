# Recorded demo: change 003 order page

Recorded by SuperDev on 2026-10-09 from the reviewed code on branch `change/003-order-page`, for spec R19. Each state used a fresh sample server started with [run_demo.py](run_demo.py). `--seed` records three status changes for order A1001 (Paid, Preparing order, Shipped). Screenshots were taken in Chrome with Playwright at 1280×860 (desktop), 390×844 (mobile) and 320 px wide. Measured values are in [evidence.json](evidence.json).

| State | Server flags | Screenshots | Evidence |
|---|---|---|---|
| Success | `--seed --demo-customer C001` | `desktop-1-success`, `mobile-1-success`, `narrow-320-success` | |
| Empty (no updates since release) | same, order A1002 | `*-2-empty` | |
| Not found (another customer's order) | same, order A1003 | `*-3-not-found-other-customer` | Same page for a missing or malformed order number |
| Loading | `--demo-delay-seconds 30` | `*-4-loading` | Taken 1.2 s after opening |
| Could not load | `--demo-fail-loads 9` | `*-5-could-not-load` | |
| Support line after 3 failed retries | `--demo-fail-loads 9`, Try again ×3 | `*-6-after-3-retries` | |
| Retry fails, then succeeds | `--demo-fail-loads 1`, Try again ×1 | `*-7a-retry-fails`, `*-7b-retry-succeeds` | |
| 10-second timeout | `--demo-delay-seconds 30` | `*-8-timeout-after-10s` | Error shown after 10.4 s (`timeout.error_shown_after_ms`) |
| Signed out | no `--demo-customer` | `*-9-signed-out` | 303 to `/sign-in?return=/orders/A1001`. `/sign-in` is not part of this sample, so it shows the 404 page, titled "Order not found" and without the demo banner |
| Session expires mid-page | signed in, then the server restarts without sign-in, then Try again | `desktop-11a-…`, `desktop-11b-…` | Ends at `/sign-in?return=/orders/A1001` (`session_expired.final_url`) |
| Keyboard focus | `--demo-fail-loads 9`, Tab | `desktop-10-keyboard-focus-try-again` | Tab reaches the Try again button, which shows a visible focus ring |
| Focus after retry | `--demo-fail-loads 2` | `desktop-12-focus-after-successful-retry` | Focus moves to the page heading (`h1`, `tabindex=-1`) after the first failure, after a failed retry and after a successful retry |
| 200% zoom | 640 CSS px at 2× (a 1280 px window at 200%) | `desktop-13-zoom-200` | No horizontal scrolling (`zoom_200.horizontal_scroll: false`) |

Not recorded:
- **Screen reader output.** The error text sits in a `role="status"` region. After a failed retry the same text is set again. Whether a screen reader reads it out a second time depends on the reader, so it needs a manual check with VoiceOver or NVDA.
- **Contrast** was calculated from the stylesheet colours in acceptance (at least 8.39:1). It was not measured on screen.
