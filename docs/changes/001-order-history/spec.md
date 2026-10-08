# Spec: Order status history for customers

References: intent.md, ux-brief.md

Terms: an **update** is one recorded status change of an order: the order id, the new status code and the time it
happened. "Recorded" means it happened after release (no backfill, `intent.md:37`).

## Requirements
- R1: The system must record an update each time an order's status changes to a different code, storing the order id,
  the new status code and a time-zone-aware timestamp, and nothing else. (verified by: unit test that changes A1001
  from `shipped` to `delivered` and checks one update with exactly those fields and an aware timestamp)
- R2: The system must not create any update for status changes made before release; orders untouched since release
  have no updates and no "Updated" time. (verified by: unit test that every sample order in `app/orders.py:12-17`
  starts with an empty history)
- R3: The system must return an order's status history to a customer only after the same ownership check as
  `status_for_customer` (`app/orders.py:37-45`): when the order is missing or belongs to another customer it must raise
  `OrderNotFound` with the same message in both cases. (verified by: unit tests for own order, other customer's order
  A1003 as C001, and missing order, checking identical exception type and message)
- R4: The system must return, for an owned order: order id, current status code and label, the time of the current
  status when it is recorded (otherwise none), and the list of updates newest first, each with code, label and time.
  (verified by: unit test with two status changes, checking order and values)
- R5: The system must show each status with the label from `status_label` (`app/orders.py:32-34`), falling back to the
  raw code for an unknown code, in both the current status and the history. (verified by: unit test with an unknown
  code such as `on_hold`)
- R6: The system must show every time in Asia/Bangkok time, in the format `9 Oct 2026, 14:05` (24-hour clock, short
  English month), and give the machine-readable value as ISO 8601 with the `+07:00` offset. (verified by: unit test
  formatting a UTC timestamp, including one that crosses midnight in Bangkok)
- R7: The system must keep the current behavior of `get_order`, `status_label`, `status_for_customer` and
  `orders_for_customer`, including their exact return values. (verified by: `tests/test_orders.py` passes without
  edits)
- R8: The system must return copies of history data, so a caller that edits the result cannot change stored updates.
  (verified by: unit test that edits the returned list and reads again)
- R9: The order status page must show the success, empty, loading and error states with the layout and copy in
  `ux-brief.md` (States and Copy), including `history.earlier_note` on every order and `history.timezone`. (verified by:
  demo of each state)
- R10: The page must check sign-in first, then ownership, then load the history. A customer who is not signed in or
  whose session expired must go through the existing sign-in flow and return to the same page, with no order data or
  order-specific message shown before sign-in. (verified by: demo signed out, then signed in as the owner and as
  another customer)
- R11: The page must show the could-not-load state when no response arrives within 10 seconds. (verified by: demo with
  a delayed response, or a test if the page code is in this repo)
- R12: The page must keep "Try again" available after every failure and, after 3 failed retries, also show
  `error.load.support`. (verified by: demo with forced failures)
- R13: The page must meet the Accessibility notes in `ux-brief.md` (one `h1` per state, `h2` sections, `ol` history with
  the accessible name "Status history, newest first", `<time datetime>` values, polite live region, focus moves,
  keyboard use, 4.5:1 contrast, 200% zoom and 320 px width). (verified by: demo with keyboard and a screen reader, and a
  contrast check)

## Edge cases
- E1: Order id that does not exist → `OrderNotFound`; page shows `error.not_found.*`, no link, no retry.
- E2: Order that belongs to another customer → exactly the same result as E1 (same message, same page, same title).
  The response never reveals that the order exists.
- E3: Order owned by the customer with no updates since release → current label without an "Updated" line,
  `history.timezone` at the top of the history section, `history.empty`, then `history.earlier_note`.
- E4: Order whose current status is recorded → it appears both under "Current status" (with "Updated …") and as the
  newest history row (PO answer 2).
- E5: Malformed order id (empty string, `None`, very long, spaces or symbols) → treated as not found (E1), never an
  unhandled error and never a different message.
- E6: Missing or empty customer id → the customer is treated as not signed in (R10) on the page; the domain function
  raises `OrderNotFound` and never returns an order.
- E7: Status "changed" to the same code it already has → no new update is recorded.
- E8: Status changed to a code with no label → the update is recorded with the raw code and shown as the raw code (R5).
- E9: Recording an update with a naive timestamp (no time zone) or for an order id that does not exist → rejected with
  an error; nothing is stored.
- E10: Two updates with the same timestamp → both shown; the one recorded later is listed first.
- E11: A change at 2026-10-09 18:30 UTC → shown as `10 Oct 2026, 01:30` (Bangkok date, not UTC date).
- E12: Cancelled order (A1004) → shown like any other status; history lists the updates that led there, if recorded.
- E13: Loading → only `page.loading`, no partial data; browser title `page.title`, or `page.loading_title` when the
  order number is not known.
- E14: A failure before the ownership check (server, network) → could-not-load state for every order id, owned or not.
- E15: No response within 10 seconds → could-not-load state. A response that arrives after the timeout is not shown;
  the customer uses "Try again".
- E16: "Try again" fails 1 or 2 times → same error copy, announced again. Third failed retry → `error.load.support`
  appears and stays until a load succeeds.
- E17: Customer opens the email link while signed in with a different account → not found (E2), and the not-found copy
  tells them to check the account.
- E18: A very long raw status code → wraps; no horizontal scrolling at 320 px.

## Flagged concerns
1. **No code changes an order's status today.** Every function in `app/orders.py:24-59` only reads. R1 needs a single
   write path (for example a `set_status` function) and every production writer of status must go through it, or the
   history will miss changes. What changes status in production (payment, warehouse, admin) is not in this repo.
   SuperDev to decide in plan.md where updates are recorded.
2. **Storage cannot keep history.** Orders live in a module-level dict in memory (`app/orders.py:1,12-17`). History
   stored there is lost on every restart. The real order store is not in this repo. If persistent storage needs a
   migration, it touches `**/migrations/**`, a risk path (`docs/risk-paths:6`). This also decides the rollback answer
   in `intent.md:27-29,42-44`.
3. **No page, handler or sign-in in this repo.** There is no HTTP handler, HTML or `app/auth*` code (ba-researcher
   searched). R9–R13 describe a page that this repo cannot build or test, and the "existing sign-in flow" (PO answer 4)
   is outside it. SuperDev to state in plan.md where the page lives and how R9–R13 are proven; if it is another repo,
   those requirements can only be verified by demo.
4. **The customer id is trusted.** `status_for_customer` uses the `customer_id` it is given (`app/orders.py:37,44`).
   The page must pass the id from the verified sign-in session, never from the URL or email link. `get_order`
   (`app/orders.py:24-29`) has no ownership check and returns None for a missing order, so the customer path must not
   use it directly.
5. **Existing test pins the return value.** `tests/test_orders.py:18-20` compares the whole dict from
   `status_for_customer`. Adding history fields there breaks R7, so history needs a new function. If `.pod/lock-tests`
   is set, tests cannot be edited to fit.
6. **Risk tier.** The findings support `Risk: high`, not lower: rollback loses data (`intent.md:27-29`), and
   persistent storage may need a migration (concern 2). Gate 2 needs the escalation signature (Lee, `pod.yml`). The
   intent's open questions are still open: whether history linked to a customer id is personal data
   (`intent.md:45-46`), and whether Lee is available and shares a GitHub login with SuperBiz (`intent.md:55-57`).
7. **Time zone without extra packages.** `app/` has no time zone code yet. `zoneinfo` is standard library but needs
   system time zone data, which some systems lack. Asia/Bangkok has no daylight saving, so a fixed `+07:00` offset
   from `datetime.timezone` also works. SuperDev to choose; the timestamp source should be the server clock in UTC.
8. **Success measure overlap.** The `delivery_date is None` errors (`logs/sample-app.log:6,7,9,11,14`) come on the same
   morning as the support tickets (`logs/sample-app.log:15`), and the code that raises them is not in this repo. Part
   of the 28 chats per week may come from that bug (`intent.md:47-50`).
9. **Support contact after failures.** R12 shows a support contact, which can add chats to the Success measure. The
   real contact (`{support_contact}` in `error.load.support`) is unknown and not guessed. The PO supplies it and decides
   whether these chats are counted in the measure.
10. **"3 failed retries" reading.** This spec reads it as the first failed load plus 3 failed "Try again" presses
    (4 failed loads in all) before `error.load.support` appears. PO to confirm.
11. **Agent-drafted copy.** In `ux-brief.md`, `error.not_found.body` was reworded to point to the confirmation email
    (PO answer 3) and `error.load.support` was added (PO answer 6). PO to approve the wording at gate 2.
12. **Personal data in logs.** `logs/sample-app.log:8` has a name and phone number. They are not copied into any
    document here; history updates must hold no personal fields (R1).

## Out of scope
- Backfill of status changes before release.
- The `delivery_date is None` bug in `logs/sample-app.log`.
- Support staff views or tools.
- A "Your orders" page or any link from the not-found message.
- Building or changing the sign-in flow.
- Notifications (email, push) when the status changes.
- Showing times in the customer's own time zone or any language other than English.
- New status codes or labels; `STATUS_LABELS` stays as it is.
- Any UI for changing an order's status.

## Decisions on flagged concerns (SuperBiz and SuperDev, before gate 2)
1. All status changes go through one new function, `set_status(order_id, status, at)`, which records history. plan.md defines it.
2. Accepted for this repo: the sample app is in-memory, so history lives for the process lifetime. Durable storage is a separate change for the real product.
3. This repo has no web layer. The deliverable is the function-level API (`status_history(customer_id, order_id)`). ux-brief.md stays as the contract for the page; R9 to R13 are proven by demo, not built here.
4. The page layer passes the signed-in customer's id. `status_history` reuses the ownership check of `status_for_customer`; `get_order` is not exposed to customers.
5. History comes from the new function; `status_for_customer` stays unchanged.
6. Risk stays high. Gate 2 and gate 4 need Lee's escalation signature.
7. Use a fixed +07:00 offset (Asia/Bangkok has no daylight saving), so no extra package is needed.
8. Accepted: the delivery_date bug is a separate change and may also move the measure; we will report both.
9. Accepted: the support contact after failures stays. We will watch whether it adds chats.
10. Confirmed: first failed load plus 3 failed "Try again" presses.
11. Confirmed: the PO approves the reworded not-found copy.
12. Out of scope here. Raised as a separate data-protection change.
