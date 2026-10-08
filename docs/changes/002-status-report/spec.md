# Spec: Order count per status for the support lead

References: intent.md (gate 1 passed, Risk: low). There is no ux-brief.md: the output is a Python function for an internal report, with no screen.

Code researched by ba-researcher: `app/orders.py`, `tests/test_orders.py`, `tests/test_order_history.py`, `docs/risk-paths`.

## Requirements
- R1: The system must provide one read-only function in `app/orders.py` that returns the number of orders in each status, counted from each order's current `status` in `_ORDERS` (`app/orders.py:17-22`), not from `_HISTORY`. (verified by: test, with the demo data the result is `Shipped: 1, Delivered: 1, Awaiting payment: 1, Cancelled: 1`, all others 0)
- R2: The system must key each count by the display text from `status_label` (`app/orders.py:71-73`), so a known code is reported under its label (e.g. `pending` → "Awaiting payment"). (verified by: test)
- R3: The system must include every label in `STATUS_LABELS` (`app/orders.py:8-15`), with 0 for labels that have no orders (today `Paid` and `Preparing order`). (verified by: test)
- R4: The system must count a status code that has no label under its raw code, the same way `status_label` shows it (PO answer 3 in intent.md; current behavior in `tests/test_order_history.py:79-85`). (verified by: test that calls `set_status("A1001", "on_hold")` and expects `on_hold: 1` and `Shipped: 0`)
- R5: The system must return the labels in `STATUS_LABELS` order first, then any raw codes with no label in sorted order, so the report reads the same every morning. (verified by: test on the key order)
- R6: The system must not include any customer identifier, order id or item in the result: only status keys and integer counts. (verified by: test that checks every key is a label or raw status and every value is an `int`, and that no `customer_id` value such as `C001` appears)
- R7: The system must not change `_ORDERS` or `_HISTORY` when called, and changing the returned value must not change stored data. (verified by: test that compares both stores before and after the call and after editing the result)
- R8: The system must return the counts so that their sum equals the number of orders in `_ORDERS`. (verified by: test)
- R9: The support lead must be able to get the morning count with one call, for the success measure (under 1 minute a day). (verified by: demo at gate 4 showing the call and its output; the time itself is self-reported for 5 working days after release, per intent.md PO answer 2)

## Edge cases
- E1: No orders at all (`_ORDERS` empty): every label in `STATUS_LABELS` is returned with 0; no error. Sum is 0.
- E2: Not-found data: a label with no orders is shown with 0 (R3), never left out.
- E3: Malformed status, unlabelled code (e.g. `on_hold`, set through `set_status`, which does not validate, `app/orders.py:54-56`): counted under the raw code (R4).
- E4: Malformed status, empty string `""`: counted under the key `""` as `status_label("")` returns it; no error. See Flagged concern 2.
- E5: Malformed status, `None` or a non-string value: the function must not raise; the order is counted under the raw value returned by `status_label`. See Flagged concern 2.
- E6: An unlabelled raw code whose text equals a label (e.g. status `"Paid"`, shown as "Paid" like code `paid`): counted together under "Paid", as the order page shows them the same way. See Flagged concern 3.
- E7: Permissions: the result has only aggregate counts, with no customer ids, order ids or items (R6), so no caller can see another customer's data through it. No existing per-customer function changes (`app/orders.py:76-122`).
- E8: Status changes between two calls: the second call reflects the current statuses only; earlier history is not counted (R1).

## Flagged concerns
1. Who may call it. Every existing read function is scoped to one customer (`app/orders.py:76-122`); this one reads across all customers, and `app/` has no internal or support-lead role. Resolved from intent: the intent says the support lead is the only user and the output has no customer identifiers (intent.md Users, Constraints), so the aggregate counts expose no personal data. The function will not be wired to any customer-facing path. Accepted as low risk; SuperDev confirms at gate 2.
2. `None`, empty or non-string statuses. `set_status` accepts any value (`app/orders.py:54-56`). The spec follows PO answer 3 (count under the raw code, as `status_label` shows it), so these become their own keys. Decision for SuperBiz: accept this, or open a separate change to validate `set_status` (out of scope here). The sort in R5 must not fail on mixed key types; SuperDev states how in plan.md.
3. Raw code that matches a label's text (E6). Counting by display text merges `"Paid"` (raw) with `paid`, which matches what the order page shows but hides the bad code. Decision for SuperBiz: accept merging (current spec), or count raw codes separately. No such data exists today (`app/orders.py:18-21`).
4. Test isolation. Tests that call `set_status` change `_ORDERS`; the history tests save and restore `_ORDERS` and `_HISTORY` in `setUp` (`tests/test_order_history.py:23-40`). New tests must do the same, or other tests' counts will change. Existing tests that must keep passing: `tests/test_orders.py:7-36`, `tests/test_order_history.py:79-122, 190-217`.
5. Risk tier. Nothing in `docs/risk-paths` matches `app/orders.py` (`docs/risk-paths:4-5` lists only `app/auth*` and `app/payment*`). ba-researcher findings do not suggest the Risk is too low; it stays low.
6. Baseline. The 15-minute starting value is demo data; the support lead confirms it in the first week (intent.md PO answer 1). Not a blocker for gate 2.

## Out of scope
- Any UI, page, CLI command, scheduled job or email for the report.
- Access control or a support-lead role in `app/`.
- Validating or rejecting status values in `set_status`.
- Counts by date, by customer, or from `_HISTORY` (trends, time in status).
- Storing, caching or exporting the report.
- Changing `STATUS_LABELS`, `status_label`, or any existing customer-facing function.

## Decisions (SuperBiz and SuperDev, before gate 2)
1. Accepted: bad status values are counted under their raw value. Validating statuses in `set_status` is a separate change.
2. Accepted: a raw code that renders like a label is counted under that label, matching the order page. No such data exists today.
