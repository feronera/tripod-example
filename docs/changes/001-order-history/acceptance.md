# Acceptance: Order status history for customers

References: intent.md (Success measure), spec.md (R1–R13, E1–E18), plan.md (Proof), review.md,
PR: GitHub PR #1 (branch `change/001-order-history`, reviewed head `4f72765`)

Status: draft. The decision below is proposed by an agent; SuperBiz confirms it at gate 4. Not signed.

## What the PR changes (plain language)
- Every time an order's status changes, the system now keeps a note of the new status and when it happened.
  There is one way to change a status, and it always writes that note.
- A customer can ask for the history of their own order. They get the current status, when it was last updated, and
  each change since release, newest first, in Bangkok time (for example `9 Oct 2026, 14:05`).
- If someone asks about an order that is not theirs, or that does not exist, they get the same "Order not found" answer,
  so nobody can tell that another customer's order exists.
- The existing order lookups work exactly as before.
- Limits in this repo: the history is kept in memory only and is lost on restart (spec decision 2). The customer
  page itself is not in this repo (spec decision 3).
- Files: `app/orders.py` (+63 lines), `app/timefmt.py` (new, 19 lines), `tests/test_order_history.py` (new, 308 lines),
  plus the change documents.

## Before acceptance
- Gate 3: `gates.log` has gate 3 owner (dan) and cross (bee) signatures. I could not run
  `scripts/gate-check.sh docs/changes/001-order-history 3` myself because this session was refused permission;
  review.md records `scripts/gate-check.sh --all` → OK (passed up to gate 3, Risk: high).
- `gates.log` has no `role=auto` line, so the PR has not been auto-merged. This is acceptance before merge.
- `.pod/kill-switch`: not present. `.pod/lock-tests`: not present at the time of this run.

## Success measure check
| Success measure | How measured | Result | Pass? |
|---|---|---|---|
| "Where is my order" plus "order status not showing" chats per week: from 28 (demo data) to 14 per week within 30 days after release | Support tool weekly report, pulled 30 days after release and compared with the 4-week average before release | Can be measured only after release. The release date is not set, so the measurement date is not set yet (see Open questions) | Not measurable yet |
| Prerequisite: customers can see when their own order's status changed, in Bangkok time | Function-level demo below (steps 1–11), plus unit tests | All 11 steps match the expected result; 136 unit tests OK | Yes (function level) |
| Prerequisite: the page shows it (R9–R13, E13–E18) | Page demo outside this repo (spec decision 3) | Not demonstrated here. The PO accepts that a later page demo proves these (see Decision) | Deferred by PO decision |

## Demo steps
review.md has no numbered demo steps of its own. It points to the plan.md "Proof" list and the spec decision 3 page
demo, so I ran the plan.md Proof steps at function level with `python3 -c` on head `4f72765`. Times passed in are UTC.
The output below is copied from the run.

1. R2: Every sample order (A1001–A1004) starts with no history.
   - Expected result: `history == []` and `updated is None` for all four.
   - Actual result: `[('A1001', [], None), ('A1002', [], None), ('A1003', [], None), ('A1004', [], None)]`. Pass.
2. R1: `set_status('A1001', 'delivered', 2026-10-09 07:05 UTC)`.
   - Expected result: returns `True`; exactly one update with `order_id`, `status` and an aware `at`; current status is `delivered`.
   - Actual result: `True`; `[StatusUpdate(order_id='A1001', status='delivered', at=datetime(2026, 10, 9, 7, 5, tzinfo=utc))]`;
     current `delivered`. Pass.
3. R4, E4, R6: `status_history('C001', 'A1001')`.
   - Expected result: current status `Delivered` with an "Updated" time, and the same change as the newest history row, in Bangkok time.
   - Actual result: `status 'delivered', label 'Delivered', updated {'text': '9 Oct 2026, 14:05', 'iso': '2026-10-09T14:05:00+07:00'}`,
     history `[{'status': 'delivered', 'label': 'Delivered', 'time': {'text': '9 Oct 2026, 14:05', ...}}]`. Pass.
4. R3, E1, E2, E5, E6: The same call with another customer (C002 for A1001), a missing id (`NOPE`), `''`, `None`, a
   1000-character id, `'A1001 '`, `'A1;001'`, a list, and an empty or `None` customer id.
   - Expected result: every case raises `OrderNotFound` with the same message; no data is returned.
   - Actual result: all 10 cases → `OrderNotFound: Order not found`. Pass.
5. E7: Set A1001 to `delivered` again.
   - Expected result: returns `False`; still one update.
   - Actual result: `False 1`. Pass.
6. R5, E8: Set A1002 to an unknown code `on_hold`.
   - Expected result: label shown as the raw code in the current status and in the history.
   - Actual result: `on_hold on_hold`. Pass.
7. R6, E11: Format 2026-10-09 07:05 UTC and 2026-10-09 18:30 UTC.
   - Expected result: `9 Oct 2026, 14:05` with ISO ending `+07:00`; `10 Oct 2026, 01:30` (Bangkok date, not UTC date).
   - Actual result: `{'text': '9 Oct 2026, 14:05', 'iso': '2026-10-09T14:05:00+07:00'}` and
     `{'text': '10 Oct 2026, 01:30', 'iso': '2026-10-10T01:30:00+07:00'}`. Pass.
8. R8: Clear the returned history list, and in a second run edit a returned row's status and time text, then read again.
   - Expected result: the stored history is unchanged.
   - Actual result: after clearing, 1 row still returned; after editing, `{'status': 'delivered', 'label': 'Delivered',
     'time': {'text': '9 Oct 2026, 14:05', ...}}`. Pass.
9. E9: `set_status` with a time without time zone (A1003), and with a missing order id (`NOPE`).
   - Expected result: both rejected; orders and history unchanged.
   - Actual result: `ValueError at must be timezone-aware`; `OrderNotFound Order not found`; unchanged `True`. Pass.
10. E10: Two changes on A1003 with the same timestamp (`paid`, then `packing`).
    - Expected result: both listed, the one recorded later first.
    - Actual result: `['packing', 'paid']`. Pass.
11. E12, R7: The cancelled order A1004 for C003, and the existing lookups.
    - Expected result: A1004 returned like any other order; `status_for_customer` and `orders_for_customer` return the same shape as before.
    - Actual result: `{'order_id': 'A1004', 'status': 'cancelled', 'label': 'Cancelled', 'updated': None, 'history': []}`;
      `status_for_customer('C001','A1002')` → `{'order_id': 'A1002', 'status': 'delivered', 'label': 'Delivered'}`;
      `git diff main -- tests/test_orders.py` is empty (0 lines). Pass.

Unit tests: `python3 -m unittest discover -s tests -t .` → `Ran 136 tests ... OK`.

Not demonstrated here: R9–R13 and E13–E18 (page states, sign-in flow, 10-second timeout, retries and
`error.load.support`, accessibility). This repo has no web layer (spec decision 3).

## PO decision on the open Major (review.md)
The PO accepts that the page states E13–E18 in ux-brief.md (and with them R9–R13) are proven by a later page demo,
outside this repo, under decision 3 in spec.md. They are not proven by this acceptance.

## Decision
Decision: accept (proposed; SuperBiz to confirm)

Reason: The demo of all 11 function-level steps from plan.md "Proof" matched the expected result (R1–R8, E1–E12),
including the safety rule that another customer's order gives exactly the same "Order not found" as a missing order
(step 4), and the Bangkok date crossing midnight (step 7). The 136 unit tests pass, and the existing lookups are unchanged
(step 11). The one open Major in review.md (E13–E18 have no proof) is resolved by the PO's decision to prove them in a
later page demo under spec decision 3. The Success measure (28 → 14 chats per week) can only be checked after release,
so this acceptance covers the feature, not the outcome.

Conditions that come with this acceptance:
- The page demo of R9–R13 and E13–E18 against ux-brief.md must be run and recorded before customers see the page. That
  demo should also show that the customer id comes from the verified session and that no route calls `set_status`
  (review.md Minor on R10).
- SuperDev runs `make check` (including `scripts/test-strength.sh` and the CODEOWNERS check) before signing gate 4.
  review.md records that these were not run as one command, and this session did not run them either.
- `Risk: high`: gate 4 also needs Lee's escalation signature, and a human merges (AGENTS.md rule 4).

## Open questions
- Release date, and so the date of the 30-day Success measure check: not set. Who pulls the support tool weekly report
  on that date (`intent.md:51-52`)?
- The 28 per week figure is demo data; the real baseline from the support tool is still needed (`intent.md:51`).
- The `delivery_date is None` bug may also move the measure (spec decision 8). How will the two effects be separated?
- Who owns the page outside this repo, and when is the R9–R13 / E13–E18 demo (`plan.md:151`)?
- `{support_contact}` for `error.load.support` is still unknown; the PO supplies it before release.
