# Spec: Order status page for customers

References: intent.md, ux-brief.md, `docs/changes/001-order-history/` (spec.md, review.md, acceptance.md)

Risk: high (intent.md). Gate 2 needs owner, cross and escalation signatures.

## Requirements
Page and data
- R1: The system must serve a read-only order status page for one order number, using the Python standard library
  only (`http.server`), and the page must get its data only through `status_history(customer_id, order_id)` in
  `app/orders.py:111-132`, never through `get_order`, `set_status`, `orders_for_customer` or `status_counts`.
  (verified by: test that the page route returns the success page for an owned order; test or code review that no
  page code path calls `set_status` or `get_order`)
- R2: The system must take the customer id only from the trusted sign-in layer (in this sample, the demo stand-in),
  never from the URL, query string, form field or any other value the browser sends. (verified by: test that a
  request for C001's session with a `customer_id` value for another customer in the query or a header still sees
  only C001's orders; demo)
- R3: The system must run the checks in this order: sign-in, then ownership, then loading the history. Ownership and
  loading may stay in one `status_history` call, as long as sign-in is checked before it. (verified by: test that a
  request with no signed-in customer never calls `status_history`)
- R4: The system must store and change no data: no page request may change `_ORDERS` or `_HISTORY`.
  (verified by: test that compares both before and after page requests in every state)

States (ux-brief.md, States and Copy)
- R5: Success. The system must show, for an owned order with recorded updates: the `h1` and browser title
  `Order {order_id}`, the current status label, the `Updated {datetime}` line when `updated` is not `None`, the
  `history.timezone` note directly under it, the "Newest first" line, the history as an `ol` newest first with one
  `{status_label} – {datetime}` row per update, and `history.earlier_note` under the list. (verified by: test on the
  rendered HTML)
- R6: Empty. The system must show, for an owned order with no recorded update: the current status label with no
  "Updated" line, `history.timezone` at the top of the history section, `history.empty`, then
  `history.earlier_note`. (verified by: test)
- R7: Not found. The system must show `error.not_found.title` as `h1` and browser title and `error.not_found.body`,
  with no link and no retry, and the same HTML, title and HTTP status for a missing order, another customer's order
  and a malformed order number. The not-found page contains nothing order-specific. (verified by: test that the
  three responses are byte-for-byte identical in status, headers that carry content and body)
- R8: Could not load. The system must show `error.load.title`, `error.load.body` and the `error.load.retry` button
  when loading fails or no response arrives within 10 seconds; the response must be the same for every order number
  when the failure happens before the ownership check. (verified by: test with a forced load failure; demo of the
  10-second timeout)
- R9: Retry and support. The system must keep "Try again" available after every failure with the same copy, and
  after 3 failed retries must also show `error.load.support` ("Still not working? Contact support at
  support@shop.example.") under `error.load.body` as plain text, not a link (PO answer 7), until the order loads.
  (verified by: demo; test of the retry counter if it lives in server-side or testable code)
- R10: Loading. The system must show only `page.loading` (no partial data) while waiting, with browser title
  `page.title`, or `page.loading_title` when the order number is not known. (verified by: demo)
- R11: Not signed in / session expired. The system must send the customer to the sign-in flow with a return to this
  page, show no order data, no order-specific message and no demo banner, and behave the same for every order
  number. (verified by: test that the response for an existing, another customer's and a missing order number is the
  same redirect; demo)
- R12: Demo banner. The system must show `Demo sign-in: Customer C001` as an `<aside aria-label="Demo notice">` before
  `main` and before the `h1` in loading, empty, success, not found and could-not-load, with identical text in every
  state and for every order number, and never in not signed in / session expired. (verified by: test on each state)
- R13: Demo-only stand-in. The system must label the demo sign-in stand-in in code as demo-only and must have a
  mechanism, chosen by SuperDev in plan.md, that keeps the stand-in and its banner out of production.
  (verified by: test or check named in plan.md; demo)

Content and accessibility
- R14: The system must use the copy in ux-brief.md "Copy" exactly, including full stops, and must show an unknown
  status code as the raw code in both current status and history, in the same style as a label. (verified by: test
  that checks each copy key's text and an `on_hold` order)
- R15: The system must show every time as `9 Oct 2026, 14:05` in Asia/Bangkok time inside
  `<time datetime="…+07:00">`, using `time_view` in `app/timefmt.py:13-19`. (verified by: test)
- R16: The system must meet the ux-brief accessibility notes: one `h1` per state, `h2` for both sections, `ol` named
  "Status history, newest first", loading and error messages in a `role="status"` live region that is cleared and
  refilled after a failed retry, focus moves (first load to `h1`; retry to `page.loading`, then to `h1` or error
  `h1`), "Try again" as the only focusable element with a visible focus outline, contrast at least 4.5:1, no
  horizontal scroll at 320 px and at 200% zoom, the support address in its own element with the full stop outside.
  (verified by: test for the markup; demo for focus, contrast, zoom and keyboard)
- R17: The system must escape every value it writes into HTML (order number, status code, label). (verified by: test
  with an order number and a status code that contain `<script>` and `"`)

Existing behavior and evidence
- R18: The system must keep every existing behavior of change 001: R1–R8 and E1–E12 of 001 `spec.md`, and all of
  `tests/test_orders.py`, `tests/test_order_history.py` and `tests/test_status_report.py` must pass without edits.
  (verified by: `make check`)
- R19: The system must have a recorded demo, before release, of every state in intent.md Success measure 2 (empty,
  loading, success, not found, could not load including the 10-second timeout and the support line after 3 failed
  retries, not signed in / session expired), which also covers 001 R9–R13 and E13–E18 and shows that the customer id
  comes from the sign-in layer and that no route calls `set_status`. (verified by: demo recorded in acceptance.md;
  closes the open Major in 001 `review.md:21-24` and the condition in 001 `acceptance.md:101-103`)

## Edge cases
Empty and not found
- E1: Owned order with no recorded update (for example after a restart, since `_HISTORY` is in memory only,
  `app/orders.py:34-35`): empty state (R6).
- E2: Owned order whose latest recorded update is not its current status: `updated` is `None`
  (`app/orders.py:122-124`), so no "Updated" line; history rows that are recorded are still listed newest first.
- E3: Order number that does not exist (for example `A9999`): not found (R7).
- E4: Request with no order number in the path: not found, with no order number in the title.

Malformed data
- E5: Order number that is empty, very long (1000 characters), contains spaces, `;`, `/`, `%00`, URL-encoded
  characters or HTML (`<script>`): not found, escaped, never an unhandled error or a 500 page.
- E6: Order number that differs only in case or has surrounding spaces (`a1001`, ` A1001`): not found; the page does
  not normalize ids (matches `_ORDERS` keys exactly).
- E7: Unknown status code (for example `on_hold`) in current status or history: shown as the raw code (R14).
- E8: A status code or label containing HTML: shown as text, escaped (R17).
- E9: Two updates with the same time: the one recorded later is listed first (`tests/test_order_history.py:242-251`).
- E10: Times that cross midnight or year end in UTC: shown in Bangkok time on the correct Bangkok date.

Permissions
- E11: C001 opens A1003 (owned by C002) or A1004 (owned by C003): not found, identical to E3 (R7). The page never
  shows, hints at or times differently for another customer's order beyond what the customer can see.
- E12: A request tries to set the customer id itself (query `?customer_id=C002`, a header, a cookie value other than
  the sign-in layer's): ignored; the signed-in customer is still used (R2).
- E13: No signed-in customer (no session, expired session, or the stand-in returns no customer): not signed in
  state for every order number, existing or not; `status_history` is not called (R3, R11).
- E14: The stand-in itself fails: could-not-load with the demo banner, same for every order number (ux-brief,
  "Demo sign-in banner" rule).
- E15: Any request method other than GET (POST, PUT, DELETE): rejected, and no data changes (R4).

States from ux-brief.md
- E16: Loading takes longer than 10 seconds: could-not-load (R8).
- E17: Load fails, then "Try again" fails 1, 2 and 3 times: same error copy each time, the live region is
  re-announced, and `error.load.support` appears only after the 3rd failed retry (R9).
- E18: Load fails, then a retry succeeds: success or empty state, the support line is gone, focus moves to the `h1`.
- E19: Session expires between the first load and "Try again": not signed in state, no order data (R11).
- E20: Long raw status code or narrow screen (320 px): text wraps, no horizontal scroll (R16).

## Flagged concerns
1. **Not signed in is indistinguishable from not found in the domain.** `status_history` raises the same
   `OrderNotFound` for a missing customer id as for a missing order (`app/orders.py:118-119`). The page must check
   sign-in itself before calling it (R3). SuperDev confirms this in plan.md.
2. **Ownership is only as strong as the caller's customer id** (001 `review.md:40-41`; rule at `app/orders.py:101-103`).
   This page is the first caller that turns a session into a customer id, so R2 and E12 carry the security weight of
   the change. Escalation should review the stand-in at gate 2 and gate 4 (PO answer, intent.md:76).
3. **Risk path.** A stand-in named `app/auth*.py` matches `docs/risk-paths:4`; touching `scripts/**`, `.github/**` or
   `pod.yml` also matches (`docs/risk-paths:4-10`). Risk is already high, so this does not raise the tier, but plan.md
   should name the files so the merge-time check agrees with intent.md.
4. **How the stand-in stays out of production** is not decided (intent.md:63-64, ux-brief Open questions). R13 needs a
   mechanism and a check in plan.md. Until then, R13 cannot be verified.
5. **How to demo not signed in** while the stand-in always signs in as C001 (ux-brief Open questions). R11 and R19
   need a demo-only way to have no signed-in customer; SuperDev chooses it in plan.md, and it must not be reachable
   in production.
6. **Same response time for not found** (ux-brief "Not found" rule). Nothing in the repo measures timing, and the
   code takes the same path for both cases (`app/orders.py:101-103`). Proposed: accept this as a risk and prove only
   identical content, title and status (R7). Human decision needed.
7. **Page location conflicts with 001.** 001 decided "This repo has no web layer ... R9 to R13 are proven by demo, not
   built here" (001 `spec.md:133`). This change builds the page here as a sample. Who owns the production page, and
   does a demo of this sample satisfy 001 `acceptance.md:101-103`? (intent.md Open questions; SuperBiz and SuperDev.)
8. **In-memory history.** `_HISTORY` is lost on restart (`app/orders.py:34-35`), so many orders will show the empty
   state (E1). This limits how much the page can move Success measure 1. Accept as a known limit or plan a separate
   change.
9. **Retry counter location.** "3 failed retries" and the 10-second timeout are client-side behavior; with the
   standard library only, this means plain JavaScript in the page or a server-side counter. Either way it needs a way
   to force failures in the demo (R8, R9). SuperDev decides in plan.md.
10. **Unhashable ids.** `status_for_customer` has no type guard and an unhashable `order_id` would raise `TypeError`
    (`app/orders.py:95-103`, inferred, no test). The page must call `status_history`, which guards it
    (`app/orders.py:118-119`). Ids from a URL path are always strings, so the risk is low.
11. **intent.md is out of date on the support contact.** It still lists `{support_contact}` as unknown
    (intent.md:73) while its PO answers supply it (intent.md:77). intent.md has passed gate 1 and was not edited here;
    SuperBiz decides whether to update and re-sign gate 1.
12. **Escalation signer.** Lee is the escalation person (`pod.yml:8-9`), but Lee's GitHub login is the same as
    SuperBiz's (`pod.yml:13,15`). For a high-risk change, confirm that the escalation signature is from a different
    person than the owner, and that Lee is available (intent.md Open questions).
13. **ux-brief.md was edited in this run** to record PO answer 7 (support address stays plain text, no `mailto:`).
    ux-brief.md had not passed a gate, so no approval is stale.
14. **Risk tier check.** The ba-researcher findings do not suggest the tier is too low; high is consistent with
    `docs/pod-charter.md:29` and `docs/risk-tiers.md:24-25`.

## Out of scope
- The real sign-in layer, sessions or accounts. Only a clearly marked demo stand-in is built.
- A production web page or deployment; this page is a sample in this repo.
- A "Your orders" list page, links between orders, or any action other than "Try again".
- A `mailto:` link or any other contact action for the support address (PO answer 7).
- Persistent storage for `_HISTORY`, and the `delivery_date is None` bug from 001.
- Changes to `app/orders.py` behavior or to `STATUS_LABELS`, new status labels, and the open 001 Minors on
  `set_status` (`review.md:27-29`, `:33-34`).
- Support staff views.
- Translations; copy is English as in ux-brief.md.
- Measuring the support-chat baseline or pulling the weekly report (intent.md Open questions).

## Decisions on flagged concerns (SuperBiz, SuperDev and Lee, before gate 2)
1. The page checks sign-in first: no signed-in customer shows the "not signed in" state before any order lookup.
2. Accepted with escalation review: the demo stand-in is the only source of the customer id in this sample. Lee reviews it at gate 2 and gate 4.
3. The stand-in is off unless the server is started with an explicit demo flag (for example `--demo-customer C001`), and the banner is always shown when it is on. The "not signed in" state is shown by starting the server without the flag. The real sign-in layer replaces the stand-in in production.
4. Accepted as a risk: equal response time for "not found" is not measured in this sample.
5. This repo builds the page as the reference sample. It satisfies change 001's open Major for the sample; the production page owner is outside this repo.
6. Known demo limitation (see README): Lee signs in git with a separate identity but shares a GitHub login with SuperBiz.
7. No change to intent.md: its PO answers section is the source of the support contact text.
